#include "read_pixels_cmd.h"

#include <maya/MFnPlugin.h>
#include <maya/MGlobal.h>


MStatus initializePlugin(MObject obj)
{
    MFnPlugin plugin(obj, "maya_playblast", "2.0.0", "Any");

    const MStatus status = plugin.registerCommand(ReadPixelsCmd::kCommandName, ReadPixelsCmd::creator, ReadPixelsCmd::newSyntax);

    if (status)
        MGlobal::displayInfo("PlayblastReadPixels v2 charge.");
    else
        MGlobal::displayError("Erreur registerCommand : " + status.errorString());

    return status;
}


MStatus uninitializePlugin(MObject obj)
{
    ReadPixelsCmd::cleanup();
    MFnPlugin plugin(obj);

    return plugin.deregisterCommand(ReadPixelsCmd::kCommandName);
}