#include "offscreen_override.h"

#include <maya/MGlobal.h>
#include <maya/MRenderTargetManager.h>
#include <maya/MDrawContext.h>
#include <cstring>

OffscreenRenderOverride::OffscreenRenderOverride(const MString& name)
    : MHWRender::MRenderOverride(name)
{}

OffscreenRenderOverride::~OffscreenRenderOverride()
{
    clearOperations();
}

MHWRender::DrawAPI OffscreenRenderOverride::supportedDrawAPIs() const
{
    return static_cast<MHWRender::DrawAPI>(MHWRender::kOpenGL | MHWRender::kOpenGLCoreProfile | MHWRender::kDirectX11);
}

void OffscreenRenderOverride::buildOperations()
{
    clearOperations();

    auto* renderer = MHWRender::MRenderer::theRenderer();
    if (renderer == nullptr)
        return;

    renderer->getStandardViewportOperations(m_ops);

    auto* captureOp = new CaptureOperation();
    m_captureOp = captureOp;
    m_ops.append(captureOp);
}

void OffscreenRenderOverride::clearOperations()
{
    m_captureOp = nullptr;
    m_ops.clear();
}

MStatus OffscreenRenderOverride::setup(const MString&)
{
    if (m_ops.length() == 0)
        buildOperations();
    return MS::kSuccess;
}

MStatus OffscreenRenderOverride::cleanup()
{
    return MS::kSuccess;
}

bool OffscreenRenderOverride::startOperationIterator()
{
    m_currentOp = 0;
    return m_ops.length() > 0;
}

MHWRender::MRenderOperation* OffscreenRenderOverride::renderOperation()
{
    if (m_currentOp >= 0 && m_currentOp < static_cast<int>(m_ops.length()))
        return m_ops[m_currentOp];
    return nullptr;
}

bool OffscreenRenderOverride::nextRenderOperation()
{
    ++m_currentOp;
    return m_currentOp < static_cast<int>(m_ops.length());
}