"""A set of distinct aspects, so they do not aggregate in analysis."""

load(":impls.bzl", "impls")

attrs = {
    "attr_aspects": ["*"],
    "attrs": {
        "_count": attr.string(default = "30000"),
        "_allocate": attr.label(
            default = "@example//memory:allocate",
            cfg = "exec",
            executable = True,
        ),
    }
}

spinlock1 = aspect(
    implementation = impls[0],
    **attrs,
)

spinlock2 = aspect(
    implementation = impls[1],
    **attrs,
)

spinlock3 = aspect(
    implementation = impls[2],
    **attrs,
)

spinlock4 = aspect(
    implementation = impls[3],
    **attrs,
)

spinlock5 = aspect(
    implementation = impls[4],
    **attrs,
)

spinlock6 = aspect(
    implementation = impls[5],
    **attrs,
)

spinlock7 = aspect(
    implementation = impls[6],
    **attrs,
)

spinlock8 = aspect(
    implementation = impls[7],
    **attrs,
)

spinlock9 = aspect(
    implementation = impls[8],
    **attrs,
)

spinlock10 = aspect(
    implementation = impls[9],
    **attrs,
)

spinlock11 = aspect(
    implementation = impls[10],
    **attrs,
)

spinlock12 = aspect(
    implementation = impls[11],
    **attrs,
)

spinlock13 = aspect(
    implementation = impls[12],
    **attrs,
)

spinlock14 = aspect(
    implementation = impls[13],
    **attrs,
)

spinlock15 = aspect(
    implementation = impls[14],
    **attrs,
)

spinlock16 = aspect(
    implementation = impls[15],
    **attrs,
)

spinlock17 = aspect(
    implementation = impls[16],
    **attrs,
)

spinlock18 = aspect(
    implementation = impls[17],
    **attrs,
)

spinlock19 = aspect(
    implementation = impls[18],
    **attrs,
)

spinlock20 = aspect(
    implementation = impls[19],
    **attrs,
)

spinlock21 = aspect(
    implementation = impls[20],
    **attrs,
)

spinlock22 = aspect(
    implementation = impls[21],
    **attrs,
)

spinlock23 = aspect(
    implementation = impls[22],
    **attrs,
)

spinlock24 = aspect(
    implementation = impls[23],
    **attrs,
)

spinlock25 = aspect(
    implementation = impls[24],
    **attrs,
)

spinlock26 = aspect(
    implementation = impls[25],
    **attrs,
)

spinlock27 = aspect(
    implementation = impls[26],
    **attrs,
)

spinlock28 = aspect(
    implementation = impls[27],
    **attrs,
)

spinlock29 = aspect(
    implementation = impls[28],
    **attrs,
)

spinlock30 = aspect(
    implementation = impls[29],
    **attrs,
)

spinlock31 = aspect(
    implementation = impls[30],
    **attrs,
)

spinlock32 = aspect(
    implementation = impls[31],
    **attrs,
)

spinlock33 = aspect(
    implementation = impls[32],
    **attrs,
)

spinlock34 = aspect(
    implementation = impls[33],
    **attrs,
)

spinlock35 = aspect(
    implementation = impls[34],
    **attrs,
)

spinlock36 = aspect(
    implementation = impls[35],
    **attrs,
)

spinlock37 = aspect(
    implementation = impls[36],
    **attrs,
)

spinlock38 = aspect(
    implementation = impls[37],
    **attrs,
)

spinlock39 = aspect(
    implementation = impls[38],
    **attrs,
)

spinlock40 = aspect(
    implementation = impls[39],
    **attrs,
)

spinlock41 = aspect(
    implementation = impls[40],
    **attrs,
)

spinlock42 = aspect(
    implementation = impls[41],
    **attrs,
)

spinlock43 = aspect(
    implementation = impls[42],
    **attrs,
)

spinlock44 = aspect(
    implementation = impls[43],
    **attrs,
)

spinlock45 = aspect(
    implementation = impls[44],
    **attrs,
)

spinlock46 = aspect(
    implementation = impls[45],
    **attrs,
)

spinlock47 = aspect(
    implementation = impls[46],
    **attrs,
)

spinlock48 = aspect(
    implementation = impls[47],
    **attrs,
)

spinlock49 = aspect(
    implementation = impls[48],
    **attrs,
)

spinlock50 = aspect(
    implementation = impls[49],
    **attrs,
)

spinlock51 = aspect(
    implementation = impls[50],
    **attrs,
)

spinlock52 = aspect(
    implementation = impls[51],
    **attrs,
)

spinlock53 = aspect(
    implementation = impls[52],
    **attrs,
)

spinlock54 = aspect(
    implementation = impls[53],
    **attrs,
)

spinlock55 = aspect(
    implementation = impls[54],
    **attrs,
)

spinlock56 = aspect(
    implementation = impls[55],
    **attrs,
)

spinlock57 = aspect(
    implementation = impls[56],
    **attrs,
)

spinlock58 = aspect(
    implementation = impls[57],
    **attrs,
)

spinlock59 = aspect(
    implementation = impls[58],
    **attrs,
)

spinlock60 = aspect(
    implementation = impls[59],
    **attrs,
)

spinlock61 = aspect(
    implementation = impls[60],
    **attrs,
)

spinlock62 = aspect(
    implementation = impls[61],
    **attrs,
)

spinlock63 = aspect(
    implementation = impls[62],
    **attrs,
)

spinlock64 = aspect(
    implementation = impls[63],
    **attrs,
)

spinlock65 = aspect(
    implementation = impls[64],
    **attrs,
)

spinlock66 = aspect(
    implementation = impls[65],
    **attrs,
)

spinlock67 = aspect(
    implementation = impls[66],
    **attrs,
)

spinlock68 = aspect(
    implementation = impls[67],
    **attrs,
)

spinlock69 = aspect(
    implementation = impls[68],
    **attrs,
)

spinlock70 = aspect(
    implementation = impls[69],
    **attrs,
)

spinlock71 = aspect(
    implementation = impls[70],
    **attrs,
)
aspects = [
    spinlock1,
    spinlock2,
    spinlock3,
    spinlock4,
    spinlock5,
    spinlock6,
    spinlock7,
    spinlock8,
    spinlock9,
    spinlock10,
    spinlock11,
    spinlock12,
    spinlock13,
    spinlock14,
    spinlock15,
    spinlock16,
    spinlock17,
    spinlock18,
    spinlock19,
    spinlock20,
    spinlock21,
    spinlock22,
    spinlock23,
    spinlock24,
    spinlock25,
    spinlock26,
    spinlock27,
    spinlock28,
    spinlock29,
    spinlock30,
    spinlock31,
    spinlock32,
    spinlock33,
    spinlock34,
    spinlock35,
    spinlock36,
    spinlock37,
    spinlock38,
    spinlock39,
    spinlock40,
    spinlock41,
    spinlock42,
    spinlock43,
    spinlock44,
    spinlock45,
    spinlock46,
    spinlock47,
    spinlock48,
    spinlock49,
    spinlock50,
    spinlock51,
    spinlock52,
    spinlock53,
    spinlock54,
    spinlock55,
    spinlock56,
    spinlock57,
    spinlock58,
    spinlock59,
    spinlock60,
    spinlock61,
    spinlock62,
    spinlock63,
    spinlock64,
    spinlock65,
    spinlock66,
    spinlock67,
    spinlock68,
    spinlock69,
    spinlock70,
    spinlock71,
]
