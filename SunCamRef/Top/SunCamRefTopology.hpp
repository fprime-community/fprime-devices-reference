// ======================================================================
// \title  SunCamRefTopology.hpp
// \brief  header for the SunCamRef topology setup/teardown functions
// ======================================================================
#ifndef SUNCAMREF_SUNCAMREFTOPOLOGY_HPP
#define SUNCAMREF_SUNCAMREFTOPOLOGY_HPP

#include <SunCamRef/Top/SunCamRefTopologyDefs.hpp>

namespace SunCamRef {

//! Initialize, connect, configure and start the topology (autocoded steps plus project configuration)
void setupTopology(const TopologyState& state);

//! Cycle the rate group driver from the Linux timer; blocks until stopRateGroups()
void startRateGroups(const Fw::TimeInterval& interval);

//! Stop the rate-group timer
void stopRateGroups();

//! Stop and tear down the topology
void teardownTopology(const TopologyState& state);

}  // namespace SunCamRef
#endif
