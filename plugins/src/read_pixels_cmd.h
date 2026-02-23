#pragma once

#include <maya/MPxCommand.h>
#include <maya/MSyntax.h>
#include <maya/MArgList.h>
#include <maya/MStatus.h>
#include <vector>
#include <cstdint>

static const char* kWidthFlag      = "-w";
static const char* kWidthFlagLong  = "-width";
static const char* kHeightFlag     = "-h";
static const char* kHeightFlagLong = "-height";
static const char* kCameraFlag     = "-cam";
static const char* kCameraFlagLong = "-camera";

class ReadPixelsCmd : public MPxCommand
{
public:
    ReadPixelsCmd()  = default;
    ~ReadPixelsCmd() override = default;

    MStatus doIt(const MArgList& args) override;

    static void*   creator();
    static MSyntax newSyntax();

    static const char* kCommandName;

    static std::vector<uint8_t> s_buffer;
    static uint32_t             s_width;
    static uint32_t             s_height;

    // Appelé depuis uninitializePlugin — détruit le override proprement
    static void cleanup();
};