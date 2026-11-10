module SunCamRef {

  # Base IDs: 0xDSSCCxxx (D = 2 for this deployment, SS = 00 main topology, CC = component).
  # Subtopologies keep their own BASE_IDs (CdhCore 0x01.., ComFprime 0x03.., DataProducts 0x04..,
  # FileHandling 0x05..).

  module Default {
    constant QUEUE_SIZE = 10
    constant STACK_SIZE = 64 * 1024
  }

  # ----------------------------------------------------------------------
  # Active component instances
  # ----------------------------------------------------------------------

  @ 1 Hz: telemetry, command dispatcher, health, events, files, data products, UART telemetry
  instance rateGroup1: Svc.ActiveRateGroup base id 0x20001000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 40

  @ 10 Hz: the unit under test (SunCamMgr.run)
  instance rateGroup2: Svc.ActiveRateGroup base id 0x20002000 \
    queue size Default.QUEUE_SIZE \
    stack size Default.STACK_SIZE \
    priority 41

  @ Unit under test (KissCam.SunCamMgr); its queue absorbs 10 Hz ticks and camera reply buffers
  instance sunCamMgr: KissCam.SunCamMgr base id 0x20003000 \
    queue size 32 \
    stack size Default.STACK_SIZE \
    priority 30

  @ Development-only gcov dump (fth dev-campaign); emits nothing unless built with -DSUNCAMREF_COVERAGE=ON
  instance covDump: SunCamRef.CovDump base id 0x20017000 \
    queue size 10 \
    stack size Default.STACK_SIZE \
    priority 20

  # ----------------------------------------------------------------------
  # Passive component instances
  # ----------------------------------------------------------------------

  instance posixTime: Svc.PosixTime base id 0x20010000

  instance rateGroupDriver: Svc.RateGroupDriver base id 0x20011000

  instance linuxTimer: Svc.LinuxTimer base id 0x20012000

  instance systemResources: Svc.SystemResources base id 0x20013000

  @ Ground link: TCP client to fprime-gds on the bench host
  instance comDriver: Drv.TcpClient base id 0x20014000

  @ Camera link: FTDI RS-422 cable, 115200 8N1 (device and baud set in SunCamRefTopology.cpp)
  instance uartDriver: Drv.PosixUartDriver base id 0x20015000

  @ Receive buffers for the UART driver (one camera line reply fits in one buffer)
  instance uartBufferManager: Svc.BufferManager base id 0x20016000

}
