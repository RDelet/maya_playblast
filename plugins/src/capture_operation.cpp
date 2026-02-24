#include "offscreen_override.h"

#include <maya/MGlobal.h>
#include <maya/MRenderTargetManager.h>
#include <maya/MDrawContext.h>
#include <cstring>

CaptureOperation::CaptureOperation()
    : MHWRender::MUserRenderOperation("PlayblastCapture")
{}

MStatus CaptureOperation::execute(const MHWRender::MDrawContext& context)
{
    ready = false;

    auto* renderer = MHWRender::MRenderer::theRenderer();
    if (renderer == nullptr) {
        MGlobal::displayError("CaptureOperation: renderer nullptr");
        return MS::kFailure;
    }

    const auto* mgr = renderer->getRenderTargetManager();
    if (mgr == nullptr) {
        MGlobal::displayError("CaptureOperation: targetManager nullptr");
        return MS::kFailure;
    }

    MStatus status;
    int     w = 0, h = 0;
    context.getRenderTargetSize(w, h);
    /*
    MGlobal::displayInfo(
        MString("CaptureOperation: renderTargetSize = ") + w + "x" + h
    );
    */

    auto* target = mgr->acquireRenderTargetFromScreen(MString("PlayblastReadback"));
    if (target == nullptr) {
        MGlobal::displayError("CaptureOperation: acquireRenderTargetFromScreen nullptr");
        return MS::kFailure;
    }

    struct TargetGuard {
        const MHWRender::MRenderTargetManager* mgr;
        MHWRender::MRenderTarget*              target;
        ~TargetGuard() { mgr->releaseRenderTarget(target); }
    } guard{ mgr, target };

    MHWRender::MRenderTargetDescription desc;
    target->targetDescription(desc);
    /*
    MGlobal::displayInfo(
        MString("CaptureOperation: target desc = ") + desc.width() + "x" + desc.height()
    );
    */

    int rowPitch   = 0;
    size_t slicePitch = 0;
    void* raw = target->rawData(rowPitch, slicePitch);
    if (raw == nullptr) {
        MGlobal::displayError("CaptureOperation: rawData nullptr");
        return MS::kFailure;
    }

    struct RawGuard {
        MHWRender::MRenderTarget* target;
        void* raw;
        ~RawGuard() { target->freeRawData(raw); }
    } rawGuard{ target, raw };

    const size_t byteCount = static_cast<size_t>(desc.width()) * desc.height() * 4;
    pixels.resize(byteCount);
    std::memcpy(pixels.data(), raw, byteCount);
    width  = static_cast<uint32_t>(desc.width());
    height = static_cast<uint32_t>(desc.height());
    ready  = true;

    //MGlobal::displayInfo("CaptureOperation: capture OK");

    return MS::kSuccess;
}