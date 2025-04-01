from pxr import Gf, Kind, Sdf, Usd, UsdGeom, UsdShade


def translate_xform(xf, translation):
    # Use the UsdGeom.XformCommonAPI to make sure we're writing
    # translations that will play nicely in applications like Maya
    xform_api = UsdGeom.XformCommonAPI(xf)
    if xform_api:
        xform_api.SetTranslate(translation)
    else:
        raise RuntimeError(f"Nontransformable prim {xf.GetPath()}")


def populate_example_material(material):
    stage = material.GetPrim().GetStage()
    preview_surface = UsdShade.Shader.Define(
        stage, material.GetPath().AppendPath("SurfaceShader")
    )
    preview_surface.CreateIdAttr("UsdPreviewSurface")
    preview_surface.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.7)
    preview_surface.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
    material.CreateSurfaceOutput().ConnectToSource(
        preview_surface.ConnectableAPI(), "surface"
    )

    uv_reader = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("UVReader"))
    uv_reader.CreateIdAttr("UsdPrimvarReader_float2")
    uv_reader.CreateInput("varname", Sdf.ValueTypeNames.Token).Set("uv")

    sampler = UsdShade.Shader.Define(stage, material.GetPath().AppendPath("Texture"))
    sampler.CreateIdAttr("UsdUVTexture")
    sampler.CreateInput("file", Sdf.ValueTypeNames.Asset).Set("confusing-logo.png")
    sampler.CreateInput("st", Sdf.ValueTypeNames.Float2).ConnectToSource(
        uv_reader.ConnectableAPI(), "result"
    )
    sampler.CreateOutput("rgb", Sdf.ValueTypeNames.Float3)
    preview_surface.CreateInput(
        "diffuseColor", Sdf.ValueTypeNames.Color3f
    ).ConnectToSource(sampler.ConnectableAPI(), "rgb")
    preview_surface.CreateInput("opacity", Sdf.ValueTypeNames.Float).ConnectToSource(
        sampler.ConnectableAPI(), "a"
    )


def populate_mesh(mesh):
    # We'll hard code some billboards to keep them simple
    mesh.CreatePointsAttr(
        [(-1.0, 0.0, -1.0), (1.0, 0.0, -1.0), (1.0, 0.0, 1.0), (-1.0, 0.0, 1.0)]
    )
    mesh.CreateFaceVertexCountsAttr([4])
    mesh.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    tex_coords = UsdGeom.PrimvarsAPI(mesh).CreatePrimvar(
        "uv", Sdf.ValueTypeNames.TexCoord2fArray, UsdGeom.Tokens.varying
    )
    tex_coords.Set([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])


def assign_material_to_mesh(material, mesh):
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim())
    UsdShade.MaterialBindingAPI(mesh).Bind(material)


def generate_ease_out(time_code_range, start, end):
    # This could be done better with numpy or an animation lib, but this
    # is good enough for our simple example.
    lerp = lambda low, high, x: low + (high - low) * x
    result = []
    duration = time_code_range[-1] - time_code_range[0]
    for tc in time_code_range:
        progress = (tc - time_code_range[0]) / duration
        scaling_factor = 1.0 - pow(1 - progress, 3)
        rot = lerp(start, end, scaling_factor)
        rotation = (0.0, rot, 0.0)
        result.append((tc, rotation))
    return result


def rotate_xform_over_time(xform, rotations):
    xform_api = UsdGeom.XformCommonAPI(xform)
    if xform_api:
        for tc, rotation in rotations:
            xform_api.SetRotate(rotation, time=tc)
    else:
        raise RuntimeError(f"Nontransformable prim {xform.GetPath()}")


def set_camera_view(camera):
    # We want one static camera for all the rendered frames. Without this,
    # usdrecord will compute a new camera on each render, and when the
    # billboards are rotated 45 degrees they are wider than the starting
    # rotation, which results in a wider camera view.
    #
    # I precomputed this to match the initial zoom that usdrecord would use.
    # The code seemed like too much to add here, so I'm hard coding the
    # camera setup.
    cam = Gf.Camera(
        transform=Gf.Matrix4d(
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.220446049250313e-16,
            1.0,
            0.0,
            0.0,
            -1.0,
            2.220446049250313e-16,
            0.0,
            0.0,
            -12.849355065402989,
            0.0,
            1.0,
        ),
        projection=Gf.Camera.Perspective,
        horizontalAperture=20.954999923706055,
        verticalAperture=15.290800094604492,
        focalLength=50.0,
    )
    camera.SetFromCamera(cam, Usd.TimeCode.Default())


def generate_example():
    # If example.usda exists this script will delete and recreate it
    stage = Usd.Stage.CreateNew("example.usda")
    if not stage:
        raise RuntimeError("Failed to create stage")
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.z)
    stage.SetMetadata(
        "comment", "An example file with attributes and relationships to query"
    )

    # Create a root model prim called Example
    world = UsdGeom.Xform.Define(stage, "/Example")
    stage.SetDefaultPrim(world.GetPrim())
    Usd.ModelAPI(world).SetKind(Kind.Tokens.component)

    # Build some prim scaffolding, we'll populate it later
    camera = UsdGeom.Camera.Define(stage, "/Camera")
    left_xf = UsdGeom.Xform.Define(stage, "/Example/Left")
    right_xf = UsdGeom.Xform.Define(stage, "/Example/Right")
    left_mesh = UsdGeom.Mesh.Define(stage, "/Example/Left/Mesh")
    right_mesh = UsdGeom.Mesh.Define(stage, "/Example/Right/Mesh")
    material = UsdShade.Material.Define(stage, "/Example/Material")

    # Fill out two identical meshes. We could put these in a
    # separate file and reference it, but I'll do it in a single
    # file to keep the example simple to read.
    populate_mesh(left_mesh)
    populate_mesh(right_mesh)

    # Translate the two meshes apart
    translate_xform(left_xf, (-1.5, 0.0, 0.0))
    translate_xform(right_xf, (1.5, 0.0, 0.0))

    # Create a material
    populate_example_material(material)

    # Assign materials
    assign_material_to_mesh(material, left_mesh)
    assign_material_to_mesh(material, right_mesh)

    # Add some rotation so we have animation to play with
    stage.SetStartTimeCode(1)
    stage.SetEndTimeCode(60)
    stage.SetTimeCodesPerSecond(30)
    rotate_xform_over_time(left_xf, generate_ease_out(range(1, 61), 0.0, 360.0))
    rotate_xform_over_time(right_xf, generate_ease_out(range(1, 61), 0.0, -720.0))

    set_camera_view(camera)

    stage.Save()


if __name__ == "__main__":
    generate_example()
