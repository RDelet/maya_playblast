#include "read_pixels_cmd.h"
#include "offscreen_override.h"

#include <maya/MArgDatabase.h>
#include <maya/MGlobal.h>
#include <maya/MString.h>
#include <maya/MStringArray.h>
#include <maya/MViewport2Renderer.h>
#include <maya/M3dView.h>

#include <memory>
#include <string>
#include <cstring>
#include <utility>

const char* ReadPixelsCmd::kCommandName = "readPixels";

std::vector<uint8_t> ReadPixelsCmd::s_buffer;
uint32_t             ReadPixelsCmd::s_width  = 0;
uint32_t             ReadPixelsCmd::s_height = 0;


// ─── OverrideDeleter — défini ici, OffscreenRenderOverride est connu ──────────
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


// ─── Cleanup appelé depuis uninitializePlugin ────────────────────────────────
void ReadPixelsCmd::cleanup()
{
    s_override.reset();
}


// ─── RAII — restaure la caméra du panel quoi qu'il arrive ───────────────────
struct CameraGuard
{
    MString panel;
    MString previous;
    bool    active = false;

    CameraGuard(const MString& p, const MString& requested)
        : panel(p), active(requested.length() > 0)
    {
        if (!active) return;
        MGlobal::executeCommand("modelPanel -q -camera " + panel, previous);
        MGlobal::executeCommand("modelPanel -e -camera " + requested + " " + panel);
    }

    ~CameraGuard()
    {
        if (active && previous.length() > 0)
            MGlobal::executeCommand(
                "modelPanel -e -camera " + previous + " " + panel
            );
    }

    CameraGuard(const CameraGuard&)            = delete;
    CameraGuard& operator=(const CameraGuard&) = delete;
};


// ─── RAII — désactive l'override sur le panel quoi qu'il arrive ─────────────
struct OverrideGuard
{
    MString panel;

    OverrideGuard(const MString& p, const MString& name) : panel(p)
    {
        MGlobal::executeCommand(
            "modelEditor -e -rendererOverrideName \"" + name + "\" " + panel
        );
    }

    ~OverrideGuard()
    {
        MGlobal::executeCommand(
            "modelEditor -e -rendererOverrideName \"\" " + panel
        );
    }

    OverrideGuard(const OverrideGuard&)            = delete;
    OverrideGuard& operator=(const OverrideGuard&) = delete;
};


// ─── Syntax ──────────────────────────────────────────────────────────────────
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


// ─── doIt ────────────────────────────────────────────────────────────────────
MStatus ReadPixelsCmd::doIt(const MArgList& argList)
{
    MStatus status;
    MArgDatabase args(syntax(), argList, &status);
    CHECK_MSTATUS_AND_RETURN_IT(status);

    auto* renderer = MHWRender::MRenderer::theRenderer();
    if (renderer == nullptr)
    {
        MGlobal::displayError("ReadPixelsCmd: MRenderer introuvable.");
        return MS::kFailure;
    }

    // Enregistre l'override une seule fois
    if (s_override == nullptr)
    {
        auto* raw = new OffscreenRenderOverride(kOverrideName);
        status = renderer->registerOverride(raw);
        if (!status)
        {
            delete raw;
            MGlobal::displayError("ReadPixelsCmd: registerOverride a echoue.");
            return MS::kFailure;
        }
        s_override.reset(raw);
    }

    // Récupère les pixels du dernier rendu
    CaptureOperation* captureOp = s_override->captureOp();
    if (captureOp == nullptr || !captureOp->ready)
    {
        MGlobal::displayError("ReadPixelsCmd: pas de pixels — appelé refresh avant ?");
        return MS::kFailure;
    }

    s_width  = captureOp->width;
    s_height = captureOp->height;
    s_buffer = std::move(captureOp->pixels);
    captureOp->ready = false;  // Reset pour la prochaine frame

    // Flip Y
    const size_t rowBytes = static_cast<size_t>(s_width) * 4;
    std::vector<uint8_t> tmp(rowBytes);
    for (uint32_t y = 0; y < s_height / 2; ++y)
    {
        auto* top = s_buffer.data() + y              * rowBytes;
        auto* bot = s_buffer.data() + (s_height-1-y) * rowBytes;
        std::memcpy(tmp.data(), top,        rowBytes);
        std::memcpy(top,        bot,        rowBytes);
        std::memcpy(bot,        tmp.data(), rowBytes);
    }

    const std::string ptrStr = std::to_string(
        reinterpret_cast<uintptr_t>(s_buffer.data())
    );
    setResult(MString(ptrStr.c_str()));
    return MS::kSuccess;
}