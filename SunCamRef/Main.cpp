// ======================================================================
// \title  Main.cpp
// \brief  main program for SunCamRef (Linux)
// ======================================================================
#include <SunCamRef/Top/SunCamRefTopology.hpp>
#include <signal.h>
#include <getopt.h>
#include <cstdlib>
#include <Os/Os.hpp>
#include <Fw/Logger/Logger.hpp>

void print_usage(const char* app) {
    Fw::Logger::log("Usage: ./%s [options]\n-a\tfprime-gds hostname/IP address\n-p\tfprime-gds port\n-u\tcamera UART device\n", app);
}

static void signalHandler(int signum) {
    SunCamRef::stopRateGroups();
}

int main(int argc, char* argv[]) {
    Os::init();
    U16 port_number = 0;
    I32 option = 0;
    char* hostname = nullptr;
    char* uart = nullptr;

    while ((option = getopt(argc, argv, "hp:a:u:")) != -1) {
        switch (option) {
            case 'a':
                hostname = optarg;
                break;
            case 'p':
                port_number = static_cast<U16>(atoi(optarg));
                break;
            case 'u':
                uart = optarg;
                break;
            case 'h':
            case '?':
            default:
                print_usage(argv[0]);
                return (option == 'h') ? 0 : 1;
        }
    }
    SunCamRef::TopologyState inputs;
    inputs.hostname = hostname;
    inputs.port = port_number;
    inputs.uartDevice = uart;

    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    Fw::Logger::log("Hit Ctrl-C to quit\n");

    SunCamRef::setupTopology(inputs);
    SunCamRef::startRateGroups(Fw::TimeInterval(0, 100000));  // 10 Hz tick
    SunCamRef::teardownTopology(inputs);
    Fw::Logger::log("Exiting...\n");
    return 0;
}
