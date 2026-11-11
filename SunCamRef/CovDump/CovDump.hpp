// ======================================================================
// \title  CovDump.hpp
// \brief  Development-only gcov dump (fth coverage-system contract); see CovDump.fpp
// ======================================================================
#ifndef SunCamRef_CovDump_HPP
#define SunCamRef_CovDump_HPP

#include "SunCamRef/CovDump/CovDumpComponentAc.hpp"

namespace SunCamRef {

class CovDump final : public CovDumpComponentBase {
  public:
    static constexpr FwSizeType MAX_OBJECTS = 8;         //!< .gcda files under the root that pass the filter
    static constexpr FwSizeType MAX_BYTES = 256 * 1024;  //!< all gcda bytes together
    static constexpr FwSizeType CHUNK = 32;              //!< bytes per CoverageChunk
    static constexpr FwSizeType CHUNKS_PER_TICK = 4;     //!< pacing: 40 events/s at 10 Hz
    static constexpr FwSizeType PATH_LEN = 512;
    static constexpr U32 MAX_DEPTH = 16;

    explicit CovDump(const char* compName);
    ~CovDump() override = default;

  private:
    void run_handler(FwIndexType portNum, U32 context) override;
    void DUMP_COVERAGE_cmdHandler(FwOpcodeType opCode, U32 cmdSeq, U16 start, U16 count) override;

    bool load(Fw::String& error);
    bool walk(const char* dir, U32 depth, Fw::String& error);
    bool readObject(const char* path, Fw::String& error);
    void emitChunk(U32 index);
    static U32 crc32(U32 crc, const U8* data, FwSizeType len);

    struct Object {
        U32 begin;       //!< offset into m_data
        U32 bytes;
        U32 nameCrc;
        U32 firstChunk;  //!< global index of its first chunk
        U32 chunks;
    };

    char m_paths[MAX_OBJECTS][PATH_LEN];
    Object m_objects[MAX_OBJECTS];
    FwSizeType m_count;
    U8 m_data[MAX_BYTES];
    FwSizeType m_used;
    U32 m_totalChunks;
    U32 m_crc;
    bool m_loaded;

    bool m_active;
    U32 m_next;
    U32 m_end;
    FwOpcodeType m_opCode;
    U32 m_cmdSeq;
};

}  // namespace SunCamRef

#endif
