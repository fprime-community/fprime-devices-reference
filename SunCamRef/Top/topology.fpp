module SunCamRef {

  enum Ports_RateGroups {
    rateGroup1
    rateGroup2
  }

  deployment topology SunCamRef {

    # ----------------------------------------------------------------------
    # Subtopology instances
    # ----------------------------------------------------------------------
    instance CdhCore.Subtopology
    instance ComFprime.Subtopology
    instance DataProducts.Subtopology
    instance FileHandling.Subtopology

    # ----------------------------------------------------------------------
    # Instances used in the topology
    # ----------------------------------------------------------------------
    instance posixTime
    instance linuxTimer
    instance rateGroupDriver
    instance rateGroup1
    instance rateGroup2
    instance systemResources
    instance comDriver
    instance uartDriver
    instance uartBufferManager
    instance sunCamMgr
    instance covDump

    # ----------------------------------------------------------------------
    # Pattern graph specifiers
    # ----------------------------------------------------------------------
    command connections instance CdhCore.cmdDisp
    event connections instance CdhCore.events
    telemetry connections instance CdhCore.tlmSend
    text event connections instance CdhCore.textLogger
    health connections instance CdhCore.$health
    param connections instance FileHandling.prmDb
    time connections instance posixTime


    # ----------------------------------------------------------------------
    # Direct graph specifiers
    # ----------------------------------------------------------------------

    connections RateGroups {
      linuxTimer.CycleOut -> rateGroupDriver.CycleIn

      # 1 Hz
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup1] -> rateGroup1.CycleIn
      rateGroup1.RateGroupMemberOut[0] -> CdhCore.Subtopology.tlmSendRun
      rateGroup1.RateGroupMemberOut[1] -> CdhCore.Subtopology.cmdDispRun
      rateGroup1.RateGroupMemberOut[2] -> CdhCore.Subtopology.healthRun
      rateGroup1.RateGroupMemberOut[3] -> CdhCore.Subtopology.eventsRun
      rateGroup1.RateGroupMemberOut[4] -> ComFprime.Subtopology.comQueueRun
      rateGroup1.RateGroupMemberOut[5] -> FileHandling.Subtopology.fileDownlinkRun
      rateGroup1.RateGroupMemberOut[6] -> FileHandling.Subtopology.fileManagerSchedIn
      rateGroup1.RateGroupMemberOut[7] -> DataProducts.Subtopology.dpBufferManagerSchedIn
      rateGroup1.RateGroupMemberOut[8] -> DataProducts.Subtopology.dpWriterSchedIn
      rateGroup1.RateGroupMemberOut[9] -> DataProducts.Subtopology.dpMgrSchedIn

      # 10 Hz
      rateGroupDriver.CycleOut[Ports_RateGroups.rateGroup2] -> rateGroup2.CycleIn
      rateGroup2.RateGroupMemberOut[0] -> sunCamMgr.run
      rateGroup2.RateGroupMemberOut[1] -> uartDriver.run
      rateGroup2.RateGroupMemberOut[2] -> uartBufferManager.schedIn
      rateGroup2.RateGroupMemberOut[3] -> systemResources.run
      rateGroup2.RateGroupMemberOut[4] -> covDump.run
    }

    connections Communications {
      comDriver.allocate   -> ComFprime.Subtopology.commsBufferGetCallee
      comDriver.deallocate -> ComFprime.Subtopology.commsBufferSendIn

      comDriver.$recv                           -> ComFprime.Subtopology.drvReceiveIn
      ComFprime.Subtopology.drvReceiveReturnOut -> comDriver.recvReturnIn

      ComFprime.Subtopology.drvSendOut -> comDriver.$send
      comDriver.ready                  -> ComFprime.Subtopology.drvConnected
    }

    connections ComFprime_CdhCore {
      CdhCore.Subtopology.eventsPktSend  -> ComFprime.Subtopology.comPacketQueueIn[ComFprime.Ports_ComPacketQueue.EVENTS]
      CdhCore.Subtopology.tlmSendPktSend -> ComFprime.Subtopology.comPacketQueueIn[ComFprime.Ports_ComPacketQueue.TELEMETRY]

      ComFprime.Subtopology.commandOut -> CdhCore.Subtopology.seqCmdBuff
      CdhCore.Subtopology.seqCmdStatus -> ComFprime.Subtopology.cmdResponseIn
    }

    connections ComFprime_FileHandling {
      FileHandling.Subtopology.fileDownlinkBufferSendOut -> ComFprime.Subtopology.bufferQueueIn[ComFprime.Ports_ComBufferQueue.FILE]
      ComFprime.Subtopology.bufferReturnOut[ComFprime.Ports_ComBufferQueue.FILE] -> FileHandling.Subtopology.fileDownlinkBufferReturn

      ComFprime.Subtopology.fileUplinkOut              -> FileHandling.Subtopology.fileUplinkBufferSendIn
      FileHandling.Subtopology.fileUplinkBufferSendOut -> ComFprime.Subtopology.fileUplinkReturnIn
    }

    connections FileHandling_DataProducts {
      DataProducts.Subtopology.dpCatFileOut             -> FileHandling.Subtopology.fileDownlinkSendFile
      FileHandling.Subtopology.fileDownlinkFileComplete -> DataProducts.Subtopology.dpCatFileDone
    }

    connections SunCam {
      # Camera UART
      uartDriver.allocate   -> uartBufferManager.bufferGetCallee
      uartDriver.deallocate -> uartBufferManager.bufferSendIn

      uartDriver.ready             -> sunCamMgr.drvConnected
      uartDriver.$recv             -> sunCamMgr.drvReceiveIn
      sunCamMgr.drvReceiveReturnOut -> uartDriver.recvReturnIn
      sunCamMgr.drvSendOut          -> uartDriver.$send

      # Image data products (synchronous get, send)
      sunCamMgr.productGetOut  -> DataProducts.Subtopology.productGetIn
      sunCamMgr.productSendOut -> DataProducts.Subtopology.productSendIn
    }

  }

}
