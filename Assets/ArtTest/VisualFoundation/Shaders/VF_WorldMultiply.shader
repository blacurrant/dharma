// Visual Foundation: world-space multiply overlay for the macro maps (albedo *= lerp(1, 2*m, opacity*w)).
// Map footprint: whole 40x40 m, U=(x+20)/40, V=(z+20)/40, clamp. Mode: _IsTint 0 = grey value map (.r), 1 = RGB tint map (0.5 neutral).
// Optional shader-side radial weight (use ONLY with the NoDamp value map): w = lerp(CenterW, 1, smoothstep(RadIn, RadOut, r)).
Shader "VF/WorldMultiply"
{
    Properties
    {
        _MainTex ("Macro map", 2D) = "grey" {}
        _Opacity ("Opacity", Range(0,1)) = 0.75
        _IsTint ("RGB tint map", Float) = 0
        _CenterW ("Weight inside combat radius", Range(0,1)) = 1
        _RadIn ("Inner radius", Float) = 8
        _RadOut ("Outer radius", Float) = 14
        _DampCenter ("Damp centre (x,z)", Vector) = (0,0,0,0)
    }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" "IgnoreProjector"="True" }
        Pass
        {
            Name "Multiply"
            Tags { "LightMode"="UniversalForward" }
            Blend DstColor Zero
            ZWrite Off
            ZTest LEqual
            Cull Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float _Opacity, _IsTint, _CenterW, _RadIn, _RadOut;
                float4 _DampCenter;
            CBUFFER_END
            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; };
            Varyings vert(Attributes v)
            {
                Varyings o; VertexPositionInputs p = GetVertexPositionInputs(v.positionOS.xyz);
                o.positionCS = p.positionCS; o.positionWS = p.positionWS; return o;
            }
            half4 frag(Varyings i) : SV_Target
            {
                float2 uv = (i.positionWS.xz + 20.0) / 40.0;
                half4 t = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, uv);
                float3 m = _IsTint > 0.5 ? t.rgb : t.rrr;
                float r = length(i.positionWS.xz - _DampCenter.xy);
                float w = lerp(_CenterW, 1.0, smoothstep(_RadIn, _RadOut, r));
                float3 mult = lerp(float3(1, 1, 1), 2.0 * m, _Opacity * w);
                return half4(mult, 1);
            }
            ENDHLSL
        }
    }
    Fallback Off
}
