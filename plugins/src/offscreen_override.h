#pragma once

#include <maya/MViewport2Renderer.h>
#include <vector>
#include <cstdint>


class CaptureOperation : public MHWRender::MUserRenderOperation
{
public:
    CaptureOperation();
    ~CaptureOperation() override = default;

    MStatus execute(const MHWRender::MDrawContext& context) override;

    std::vector<uint8_t> pixels;
    uint32_t             width  = 0;
    uint32_t             height = 0;
    bool                 ready  = false;
};


class OffscreenRenderOverride : public MHWRender::MRenderOverride
{
public:
    explicit OffscreenRenderOverride(const MString& name);
    ~OffscreenRenderOverride() override;

    // Non-copiable, non-movable — Maya conserve un pointeur brut
    OffscreenRenderOverride(const OffscreenRenderOverride&)            = delete;
    OffscreenRenderOverride& operator=(const OffscreenRenderOverride&) = delete;
    OffscreenRenderOverride(OffscreenRenderOverride&&)                 = delete;
    OffscreenRenderOverride& operator=(OffscreenRenderOverride&&)      = delete;

    MHWRender::DrawAPI           supportedDrawAPIs()  const override;
    bool                         startOperationIterator()    override;
    MHWRender::MRenderOperation* renderOperation()           override;
    bool                         nextRenderOperation()       override;
    MStatus                      setup(const MString& dest)  override;
    MStatus                      cleanup()                   override;
    MString                      uiName()             const override
        { return MString("Playblast Offscreen"); }

    // Pointeur observateur non-owning — MRenderOperationList est propriétaire
    [[nodiscard]] CaptureOperation* captureOp() const { return m_captureOp; }

private:
    void buildOperations();
    void clearOperations();

    MHWRender::MRenderOperationList m_ops;
    int                             m_currentOp = -1;
    CaptureOperation*               m_captureOp = nullptr;  // non-owning
};