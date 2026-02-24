#pragma once

#include "capture_operation.h"

#include <maya/MViewport2Renderer.h>
#include <vector>
#include <cstdint>


class OffscreenRenderOverride : public MHWRender::MRenderOverride
{
    public:
        explicit OffscreenRenderOverride(const MString& name);
        ~OffscreenRenderOverride() override;

        OffscreenRenderOverride(const OffscreenRenderOverride&) = delete;
        OffscreenRenderOverride&    operator=(const OffscreenRenderOverride&) = delete;
        OffscreenRenderOverride(OffscreenRenderOverride&&) = delete;
        OffscreenRenderOverride&    operator=(OffscreenRenderOverride&&) = delete;

        MHWRender::DrawAPI           supportedDrawAPIs()  const override;
        bool                         startOperationIterator() override;
        MHWRender::MRenderOperation* renderOperation() override;
        bool                         nextRenderOperation() override;
        MStatus                      setup(const MString& dest) override;
        MStatus                      cleanup() override;
        MString                      uiName() const override { return MString("Playblast Offscreen"); }

        [[nodiscard]] CaptureOperation* captureOp() const { return m_captureOp; }

    private:
        void buildOperations();
        void clearOperations();

        MHWRender::MRenderOperationList m_ops;
        int                             m_currentOp = -1;
        CaptureOperation*               m_captureOp = nullptr;
};