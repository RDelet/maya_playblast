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