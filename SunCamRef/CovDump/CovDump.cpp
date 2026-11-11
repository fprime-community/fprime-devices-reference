// ======================================================================
// \title  CovDump.cpp
// \brief  Development-only gcov dump (fth coverage-system contract); see CovDump.fpp
// ======================================================================
#include "SunCamRef/CovDump/CovDump.hpp"

#include <dirent.h>
#include <sys/stat.h>
#include <cstdio>
#include <cstring>

#include "Fw/Types/Assert.hpp"

// Hosted libgcov entry point. A strong reference is needed to pull it out of libgcov.a in the instrumented
// build; the uninstrumented (RfR) image has no libgcov and must not reference it at all.
#if defined(SUNCAMREF_COVERAGE)
extern "C" void __gcov_dump(void);
static void (*const gcovDump)(void) = __gcov_dump;
#else
static void (*const gcovDump)(void) = nullptr;
#endif

#ifndef SUNCAMREF_GCDA_ROOT
#define SUNCAMREF_GCDA_ROOT ""  // set by the SUNCAMREF_COVERAGE build option to the build cache
#endif
#ifndef SUNCAMREF_GCDA_FILTER
#define SUNCAMREF_GCDA_FILTER "/SunCamMgr/"  // only the UUT's objects are dumped
#endif

namespace SunCamRef {

CovDump::CovDump(const char* const compName)
    : CovDumpComponentBase(compName),
      m_count(0),
      m_used(0),
      m_totalChunks(0),
      m_crc(0),
      m_loaded(false),
      m_active(false),
      m_next(0),
      m_end(0),
      m_opCode(0),
      m_cmdSeq(0) {
    ::memset(this->m_paths, 0, sizeof(this->m_paths));
    ::memset(this->m_objects, 0, sizeof(this->m_objects));
}

U32 CovDump::crc32(U32 crc, const U8* const data, const FwSizeType len) {
    // IEEE 802.3 reflected CRC-32, zlib.crc32(data, crc) chaining
    U32 c = crc ^ 0xFFFFFFFFu;
    for (FwSizeType i = 0; i < len; i++) {
        c ^= data[i];
        for (U32 k = 0; k < 8; k++) {
            c = (c >> 1) ^ (0xEDB88320u & (0u - (c & 1u)));
        }
    }
    return c ^ 0xFFFFFFFFu;
}

bool CovDump::readObject(const char* const path, Fw::String& error) {
    FILE* const f = ::fopen(path, "rb");
    if (f == nullptr) {
        error.format("cannot open %s", path);
        return false;
    }
    FwSizeType n = 0;
    while (true) {
        if (this->m_used + n >= MAX_BYTES) {
            ::fclose(f);
            error.format("gcda bytes exceed %u", static_cast<unsigned>(MAX_BYTES));
            return false;
        }
        const size_t got = ::fread(&this->m_data[this->m_used + n], 1, MAX_BYTES - this->m_used - n, f);
        n += got;
        if (got == 0) {
            break;
        }
    }
    const bool readError = (::ferror(f) != 0);
    ::fclose(f);
    if (readError) {
        error.format("read error on %s", path);
        return false;
    }
    if (n == 0) {
        return true;  // an empty gcda carries no counters: skipped
    }
    Object& o = this->m_objects[this->m_count];
    o.begin = static_cast<U32>(this->m_used);
    o.bytes = static_cast<U32>(n);
    o.nameCrc = crc32(0, reinterpret_cast<const U8*>(path), ::strlen(path));
    o.firstChunk = this->m_totalChunks;
    o.chunks = static_cast<U32>((n + CHUNK - 1) / CHUNK);
    this->m_crc = crc32(this->m_crc, &this->m_data[this->m_used], n);
    this->m_used += n;
    this->m_totalChunks += o.chunks;
    this->m_count++;
    return true;
}

bool CovDump::walk(const char* const dir, const U32 depth, Fw::String& error) {
    if (depth > MAX_DEPTH) {
        return true;
    }
    DIR* const d = ::opendir(dir);
    if (d == nullptr) {
        error.format("cannot open directory %s", dir);
        return false;
    }
    bool ok = true;
    for (struct dirent* e = ::readdir(d); ok && e != nullptr; e = ::readdir(d)) {
        if (::strcmp(e->d_name, ".") == 0 || ::strcmp(e->d_name, "..") == 0) {
            continue;
        }
        char path[PATH_LEN];
        const int len = ::snprintf(path, sizeof(path), "%s/%s", dir, e->d_name);
        if (len <= 0 || static_cast<size_t>(len) >= sizeof(path)) {
            continue;  // too long to be one of ours
        }
        struct stat st;
        if (::lstat(path, &st) != 0) {
            continue;
        }
        if (S_ISDIR(st.st_mode)) {
            ok = this->walk(path, depth + 1, error);
        } else if (S_ISREG(st.st_mode)) {
            const size_t plen = ::strlen(path);
            const bool gcda = plen > 5 && ::strcmp(&path[plen - 5], ".gcda") == 0;
            if (gcda && ::strstr(path, SUNCAMREF_GCDA_FILTER) != nullptr) {
                if (this->m_count >= MAX_OBJECTS) {
                    error.format("more than %u gcda files match", static_cast<unsigned>(MAX_OBJECTS));
                    ok = false;
                } else {
                    // keep the list sorted by path so the object order is deterministic
                    FwSizeType pos = this->m_count;
                    while (pos > 0 && ::strcmp(this->m_paths[pos - 1], path) > 0) {
                        pos--;
                    }
                    for (FwSizeType k = this->m_count; k > pos; k--) {
                        ::memcpy(this->m_paths[k], this->m_paths[k - 1], PATH_LEN);
                    }
                    ::memcpy(this->m_paths[pos], path, plen + 1);
                    this->m_count++;
                }
            }
        }
    }
    ::closedir(d);
    return ok;
}

bool CovDump::load(Fw::String& error) {
    this->m_loaded = false;
    this->m_count = 0;
    this->m_used = 0;
    this->m_totalChunks = 0;
    this->m_crc = 0;
    if (::strlen(SUNCAMREF_GCDA_ROOT) == 0) {
        error = "no gcda root: image not built with SUNCAMREF_COVERAGE";
        return false;
    }
    if (gcovDump != nullptr) {
        gcovDump();  // hosted libgcov: counters -> .gcda (merged with earlier process lives)
    } else {
        error = "no libgcov in this image (SUNCAMREF_COVERAGE build without instrumentation)";
        return false;
    }
    if (!this->walk(SUNCAMREF_GCDA_ROOT, 0, error)) {
        return false;
    }
    const FwSizeType found = this->m_count;
    this->m_count = 0;
    for (FwSizeType i = 0; i < found; i++) {
        if (!this->readObject(this->m_paths[i], error)) {
            return false;
        }
    }
    if (this->m_count == 0) {
        error.format("no .gcda matching %s under the gcda root", SUNCAMREF_GCDA_FILTER);
        return false;
    }
    this->m_loaded = true;
    return true;
}

void CovDump::emitChunk(const U32 index) {
    FwSizeType oi = 0;
    while (oi + 1 < this->m_count && index >= this->m_objects[oi + 1].firstChunk) {
        oi++;
    }
    const Object& o = this->m_objects[oi];
    const U32 offset = (index - o.firstChunk) * static_cast<U32>(CHUNK);
    const U32 length = (o.bytes - offset < CHUNK) ? (o.bytes - offset) : static_cast<U32>(CHUNK);
    U32 words[8] = {0, 0, 0, 0, 0, 0, 0, 0};
    for (U32 i = 0; i < length; i++) {
        words[i / 4] |= static_cast<U32>(this->m_data[o.begin + offset + i]) << (8 * (3 - (i % 4)));
    }
    this->log_ACTIVITY_LO_CoverageChunk(static_cast<U16>(oi), offset, static_cast<U8>(length), words[0], words[1],
                                        words[2], words[3], words[4], words[5], words[6], words[7]);
    if (index + 1 == o.firstChunk + o.chunks) {
        this->log_ACTIVITY_LO_CoverageObject(static_cast<U16>(oi), o.nameCrc, o.bytes);
    }
}

void CovDump::run_handler(const FwIndexType portNum, const U32 context) {
    if (!this->m_active) {
        return;
    }
    for (FwSizeType i = 0; i < CHUNKS_PER_TICK && this->m_next < this->m_end; i++) {
        this->emitChunk(this->m_next);
        this->m_next++;
    }
    if (this->m_next >= this->m_end) {
        if (this->m_next >= this->m_totalChunks) {
            this->log_ACTIVITY_HI_CoverageDumpDone(static_cast<U16>(this->m_count), static_cast<U32>(this->m_used),
                                                  this->m_crc);
        }
        this->m_active = false;
        this->cmdResponse_out(this->m_opCode, this->m_cmdSeq, Fw::CmdResponse::OK);
    }
}

void CovDump::DUMP_COVERAGE_cmdHandler(const FwOpcodeType opCode, const U32 cmdSeq, const U16 start, const U16 count) {
    if (this->m_active) {
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::BUSY);
        return;
    }
    Fw::String error;
    if ((start == 0 || !this->m_loaded) && !this->load(error)) {
        this->log_WARNING_HI_CoverageDumpError(error);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }
    if (start >= this->m_totalChunks) {
        error.format("start %u beyond the %u chunks", static_cast<unsigned>(start),
                     static_cast<unsigned>(this->m_totalChunks));
        this->log_WARNING_HI_CoverageDumpError(error);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::VALIDATION_ERROR);
        return;
    }
    const U32 end = (count == 0) ? this->m_totalChunks : static_cast<U32>(start) + count;
    this->m_next = start;
    this->m_end = (end > this->m_totalChunks) ? this->m_totalChunks : end;
    this->m_opCode = opCode;
    this->m_cmdSeq = cmdSeq;
    this->m_active = true;  // the response follows the last chunk (run_handler)
}

}  // namespace SunCamRef
