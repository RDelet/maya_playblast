#include "read_pixels_cmd.h"
#include "capture_operation.h"
#include "offscreen_override.h"

#include <maya/MArgDatabase.h>
#include <maya/MGlobal.h>
#include <maya/MString.h>
#include <maya/MViewport2Renderer.h>
#include <maya/M3dView.h>

#include <memory>
#include <string>
#include <cstring>

const char* ReadPixelsCmd::kCommandName = "readPixels";

std::vector<uint8_t> ReadPixelsCmd::s_buffer;
uint32_t             ReadPixelsCmd::s_width  = 0;
uint32_t             ReadPixelsCmd::s_height = 0;


struct OverrideDeleter {
    void operator()(OffscreenRenderOverride* ptr) const noexcept {
        if (ptr == nullptr) return;
        auto* renderer = MHWRender::MRenderer::theRenderer();
        if (renderer != nullptr)
            renderer->deregisterOverride(ptr);
        delete ptr;
    }
};

using OverridePtr = std::unique_ptr<OffscreenRenderOverride, OverrideDeleter>;

static OverridePtr   s_override;
static const MString kOverrideName("PlayblastOffscreenOverride");


void ReadPixelsCmd::cleanup()
{
    s_override.reset();
}

MSyntax ReadPixelsCmd::newSyntax()
{
    MSyntax syntax;
    syntax.addFlag(kWidthFlag,  kWidthFlagLong,  MSyntax::kLong);
    syntax.addFlag(kHeightFlag, kHeightFlagLong, MSyntax::kLong);
    syntax.addFlag(kCameraFlag, kCameraFlagLong, MSyntax::kString);
    return syntax;
}

void* ReadPixelsCmd::creator()
{
    return new ReadPixelsCmd();
}

struct ViewOverrideGuard
{
    M3dView& view;
    
    ViewOverrideGuard(M3dView& v, const MString& overrideName) : view(v)
    {
        view.setRenderOverrideName(overrideName);
    }
    ~ViewOverrideGuard()
    {
        view.setRenderOverrideName(MString(""));
    }

    ViewOverrideGuard(const ViewOverrideGuard&) = delete;
    ViewOverrideGuard& operator=(const ViewOverrideGuard&) = delete;
};


MStatus ReadPixelsCmd::doIt(const MArgList& argList)
{
    MStatus status;
    MArgDatabase args(syntax(), argList, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    auto* renderer = MHWRender::MRenderer::theRenderer();
    if (renderer == nullptr)
    {
        MGlobal::displayError("ReadPixelsCmd: MRenderer not found.");
        return MS::kFailure;
    }

    if (s_override == nullptr)
    {
        auto* raw = new OffscreenRenderOverride(kOverrideName);
        status = renderer->registerOverride(raw);
        if (!status)
        {
            delete raw;
            MGlobal::displayError("ReadPixelsCmd: registerOverride failed.");
            return MS::kFailure;
        }
        s_override.reset(raw);
    }

    M3dView activeView = M3dView::active3dView(&status);
    if (!status)
    {
        MGlobal::displayError("ReadPixelsCmd: could not get active 3d view.");
        return MS::kFailure;
    }

    {
        ViewOverrideGuard guard(activeView, kOverrideName);
        activeView.refresh(false, true);
    }

    CaptureOperation* captureOp = s_override->captureOp();
    if (captureOp == nullptr || !captureOp->ready)
    {
        MGlobal::displayError("ReadPixelsCmd: capture failed after forced refresh.");
        return MS::kFailure;
    }

    s_width  = captureOp->width;
    s_height = captureOp->height;
    s_buffer = std::move(captureOp->pixels);
    captureOp->ready = false;

    const std::string ptrStr = std::to_string(
        reinterpret_cast<uintptr_t>(s_buffer.data())
    );
    setResult(MString(ptrStr.c_str()));

    return MS::kSuccess;
}