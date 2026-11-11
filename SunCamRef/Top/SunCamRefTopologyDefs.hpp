// ======================================================================
// \title  SunCamRefTopologyDefs.hpp
// \brief  definitions required by the topology autocoder for SunCamRef
// ======================================================================
#ifndef SUNCAMREF_SUNCAMREFTOPOLOGYDEFS_HPP
#define SUNCAMREF_SUNCAMREFTOPOLOGYDEFS_HPP

#include "Fw/Types/MemAllocator.hpp"
#include "SunCamRef/Top/FppConstantsAc.hpp"

// Subtopology PingEntries includes
#include "Svc/Subtopologies/CdhCore/PingEntries.hpp"
#include "Svc/Subtopologies/ComFprime/PingEntries.hpp"
#include "Svc/Subtopologies/DataProducts/PingEntries.hpp"
#include "Svc/Subtopologies/FileHandling/PingEntries.hpp"

// SubtopologyTopologyDefs includes
#include "Svc/Subtopologies/CdhCore/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/ComFprime/SubtopologyTopologyDefs.hpp"
// ComFprime's SubtopologyTopologyDefs.hpp at fprime f28d2da does not include its queue-index enums (ComCcsds's does)
#include "Svc/Subtopologies/ComFprime/Ports_ComBufferQueueEnumAc.hpp"
#include "Svc/Subtopologies/ComFprime/Ports_ComPacketQueueEnumAc.hpp"
#include "Svc/Subtopologies/DataProducts/SubtopologyTopologyDefs.hpp"
#include "Svc/Subtopologies/FileHandling/SubtopologyTopologyDefs.hpp"

namespace PingEntries {
namespace SunCamRef_rateGroup1 {
enum { WARN = 3, FATAL = 5 };
}
namespace SunCamRef_rateGroup2 {
enum { WARN = 3, FATAL = 5 };
}
namespace SunCamRef_sunCamMgr {
enum { WARN = 3, FATAL = 5 };
}
}  // namespace PingEntries

namespace SunCamRef {

extern Fw::MemAllocator& memAllocator;

//! State handed to setupTopology: command line inputs
struct TopologyState {
    const char* hostname;                         //!< fprime-gds host (TCP)
    U16 port;                                     //!< fprime-gds port (TCP)
    const char* uartDevice;                       //!< camera UART device
    CdhCore::SubtopologyState cdhCore;            //!< Subtopology state for CdhCore
    ComFprime::SubtopologyState comFprime;        //!< Subtopology state for ComFprime
    DataProducts::SubtopologyState dataProducts;  //!< Subtopology state for DataProducts
    FileHandling::SubtopologyState fileHandling;  //!< Subtopology state for FileHandling
};

namespace PingEntries = ::PingEntries;
}  // namespace SunCamRef
#endif
