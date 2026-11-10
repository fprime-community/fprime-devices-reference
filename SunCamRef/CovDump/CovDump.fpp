module SunCamRef {

  @ Development-only gcov dump for `fth dev-campaign` (harness skill §3a). DUMP_COVERAGE flushes the hosted
  @ libgcov counters (`__gcov_dump`, weak: a no-op in an uninstrumented image), reads the `.gcda` files the
  @ instrumented build writes under its build cache and emits them as CoverageChunk / CoverageObject /
  @ CoverageDumpDone events (fth `coverage-system` contract), paced from the rate-group port. Not part of the
  @ UUT; the RfR verdicts come from the uninstrumented image, where this command reports "no gcda root".
  active component CovDump {

    @ Emit chunks [start, start + count) of the gcda stream; count 0 = to the end. start 0 (re)loads the files.
    async command DUMP_COVERAGE(
        start: U16 @< first global 32-byte chunk index
        count: U16 @< chunks to emit (0 = all remaining)
      ) opcode 0

    @ Pacing tick (10 Hz): a few chunks per call so the event path never bursts
    async input port run: Svc.Sched

    @ Up to 32 gcda bytes of one object, MSB-first packed into eight words (zero padded)
    event CoverageChunk(object: U16, offset: U32, length: U8, data0: U32, data1: U32, data2: U32, data3: U32,
                        data4: U32, data5: U32, data6: U32, data7: U32) \
      severity activity low id 0 \
      format "coverage chunk obj {} off {} len {}: {x} {x} {x} {x} {x} {x} {x} {x}"

    @ After an object's last chunk: CRC-32 (IEEE) of the .gcda path the compiler recorded, and its size
    event CoverageObject(object: U16, nameCrc: U32, bytes: U32) \
      severity activity low id 1 \
      format "coverage object {} name-crc {x}: {} bytes"

    @ Once the walk reaches the end: object count, total bytes, CRC-32 over all gcda bytes in object order
    event CoverageDumpDone(objects: U16, totalBytes: U32, crc: U32) \
      severity activity high id 2 \
      format "coverage dump done: {} objects, {} bytes, crc {x}"

    @ The dump could not be produced (no gcda root, too many/large objects, unreadable file, bad range)
    event CoverageDumpError(reason: string size 96) \
      severity warning high id 3 \
      format "coverage dump error: {}"

    command recv port cmdIn
    command reg port cmdRegOut
    command resp port cmdResponseOut
    event port eventOut
    text event port textEventOut
    time get port timeGetOut
  }
}
