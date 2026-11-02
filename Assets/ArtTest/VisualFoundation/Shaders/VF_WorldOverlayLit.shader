// Visual Foundation: world-space lit overlay (alpha-lerp on albedo, lit by the scene's URP lights/probes/shadows).
// Art-test only; does not touch any shared URP asset. Mapping modes follow VF_PALETTE_USAGE_NOTE.md:
//   0 floor planar  u = x/TileU, v = z/TileV   (up-facing quads only)
//   1 wall on an X-facing plane   u = x/TileU, v = y/TileV
//   2 wall on a Z-facing plane    u = z/TileU, v = y/TileV
//   3 decal: mesh UV 0..1 (soot smudges), rotate the quad per instance
// Radial weight: w = lerp(CenterW, 1, smoothstep(RadIn, RadOut, |xz - DampCenter|)) multiplies alpha.
Shader "VF/WorldOverlayLit"
{
    Properties
    {
        _MainTex ("Overlay (RGBA)", 2D) = "white" {}
        _Opacity ("Opacity", Range(0,1)) = 0.5
        _TileU ("Tile U metres", Float) = 2
        _TileV ("Tile V metres", Float) = 2
        _MapMode ("Map mode", Float) = 0
        _CenterW ("Weight inside combat radius", Range(0,1)) = 1
        _RadIn ("Inner radius", Float) = 10
        _RadOut ("Outer radius", Float) = 14
        _DampCenter ("Damp centre (x,z)", Vector) = (0,0,0,0)
        _VClip ("Clip v outside 0..1", Float) = 0
        _CellVar ("Per-cell mirror/rotate (mode 0)", Float) = 0
        _Rot ("Floor map rotation degrees (mode 0)", Float) = 0
        _UVOff ("UV offset in tiles (mode 0)", Vector) = (0,0,0,0)
        _Smooth ("Smoothness", Range(0,1)) = 0.05
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" "IgnoreProjector"="True" }
        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            ZTest LEqual
            Offset -1, -1
            Cull Off
            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile _ _LIGHT_LAYERS
            #pragma multi_compile_fog
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float _Opacity, _TileU, _TileV, _MapMode, _CenterW, _RadIn, _RadOut, _VClip, _Smooth, _Rot, _CellVar;
                float4 _DampCenter, _UVOff;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
                half fogFactor : TEXCOORD3;
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS;
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                o.uv = v.uv; o.fogFactor = ComputeFogFactor(p.positionCS.z);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                float3 wp = i.positionWS;
                float2 uv;
                if (_MapMode < 0.5) { float cr = cos(radians(_Rot)), sr = sin(radians(_Rot)); float2 q = float2(cr * wp.x - sr * wp.z, sr * wp.x + cr * wp.z); uv = float2(q.x / _TileU, q.y / _TileV) + _UVOff.xy; }
                else if (_MapMode < 1.5) uv = float2(wp.x / _TileU, wp.y / _TileV);
                else if (_MapMode < 2.5) uv = float2(wp.z / _TileU, wp.y / _TileV);
                else uv = i.uv;
                half4 t;
                if (_MapMode < 0.5 && _CellVar > 0.5)
                {
                    float2 cell = floor(uv); float2 f = frac(uv);
                    float h = frac(sin(dot(cell, float2(12.9898, 78.233))) * 43758.5453) * 8.0; int hi = (int)floor(h);
                    float2 gx = ddx(uv), gy = ddy(uv); float2 p = f - 0.5;
                    if ((hi & 1) != 0) { p.x = -p.x; gx.x = -gx.x; gy.x = -gy.x; }
                    int k = (hi >> 1) & 3;
                    for (int j = 0; j < k; j++) { p = float2(-p.y, p.x); gx = float2(-gx.y, gx.x); gy = float2(-gy.y, gy.x); }
                    t = SAMPLE_TEXTURE2D_GRAD(_MainTex, sampler_MainTex, p + 0.5, gx, gy);
                }
                else t = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv);
                float r = length(wp.xz - _DampCenter.xy);
                float w = lerp(_CenterW, 1.0, smoothstep(_RadIn, _RadOut, r));
                float a = t.a * _Opacity * w;
                if (_VClip > 0.5) a *= smoothstep(0.0, 0.05, uv.y) * smoothstep(1.0, 0.95, uv.y);
                clip(a - 0.002);

                float3 V = GetWorldSpaceNormalizeViewDir(wp);
                float3 n = normalize(i.normalWS);
                if (dot(n, V) < 0) n = -n;
                if (_MapMode < 0.5) n = float3(0, 1, 0);

                InputData inputData = (InputData)0;
                inputData.positionWS = wp;
                inputData.normalWS = n;
                inputData.viewDirectionWS = V;
                inputData.shadowCoord = TransformWorldToShadowCoord(wp);
                inputData.fogCoord = InitializeInputDataFog(float4(wp, 1.0), i.fogFactor);
                inputData.vertexLighting = half3(0, 0, 0);
                inputData.bakedGI = SampleSH(n);
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                inputData.shadowMask = half4(1, 1, 1, 1);

                SurfaceData s = (SurfaceData)0;
                s.albedo = t.rgb; s.metallic = 0; s.specular = 0; s.smoothness = _Smooth;
                s.occlusion = 1; s.alpha = a; s.normalTS = half3(0, 0, 1);

                half4 c = UniversalFragmentPBR(inputData, s);
                c.rgb = MixFog(c.rgb, inputData.fogCoord);
                c.a = a;
                return c;
            }
            ENDHLSL
        }
    }
    Fallback Off
}
