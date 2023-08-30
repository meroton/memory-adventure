"""A set of distinct rules, so they do not aggregate in analysis."""

load(":aspects.bzl", "aspects")
load(":impl.bzl", "spinlock_rule_impl")

def factory(index):
    spin = rule(
        implementation = spinlock_rule_impl,
        attrs = {
            "srcs": attr.label_list(
            aspects = [aspects[index - 1]]),
        },
    )

    return spin

spin1 = factory(1)
spin2 = factory(2)
spin3 = factory(3)
spin4 = factory(4)
spin5 = factory(5)
spin6 = factory(6)
spin7 = factory(7)
spin8 = factory(8)
spin9 = factory(9)
spin10 = factory(10)
spin11 = factory(11)
spin12 = factory(12)
spin13 = factory(13)
spin14 = factory(14)
spin15 = factory(15)
spin16 = factory(16)
spin17 = factory(17)
spin18 = factory(18)
spin19 = factory(19)
spin20 = factory(20)
spin21 = factory(21)
spin22 = factory(22)
spin23 = factory(23)
spin24 = factory(24)
spin25 = factory(25)
spin26 = factory(26)
spin27 = factory(27)
spin28 = factory(28)
spin29 = factory(29)
spin30 = factory(30)
spin31 = factory(31)
spin32 = factory(32)
spin33 = factory(33)
spin34 = factory(34)
spin35 = factory(35)
spin36 = factory(36)
spin37 = factory(37)
spin38 = factory(38)
spin39 = factory(39)
spin40 = factory(40)
spin41 = factory(41)
spin42 = factory(42)
spin43 = factory(43)
spin44 = factory(44)
spin45 = factory(45)
spin46 = factory(46)
spin47 = factory(47)
spin48 = factory(48)
spin49 = factory(49)
spin50 = factory(50)
spin51 = factory(51)
spin52 = factory(52)
spin53 = factory(53)
spin54 = factory(54)
spin55 = factory(55)
spin56 = factory(56)
spin57 = factory(57)
spin58 = factory(58)
spin59 = factory(59)
spin60 = factory(60)
spin61 = factory(61)
spin62 = factory(62)
spin63 = factory(63)
spin64 = factory(64)
spin65 = factory(65)
spin66 = factory(66)
spin67 = factory(67)
spin68 = factory(68)
spin69 = factory(69)
spin70 = factory(70)
spin71 = factory(71)

rules = [
    spin1,
    spin2,
    spin3,
    spin4,
    spin5,
    spin6,
    spin7,
    spin8,
    spin9,
    spin10,
    spin11,
    spin12,
    spin13,
    spin14,
    spin15,
    spin16,
    spin17,
    spin18,
    spin19,
    spin20,
    spin21,
    spin22,
    spin23,
    spin24,
    spin25,
    spin26,
    spin27,
    spin28,
    spin29,
    spin30,
    spin31,
    spin32,
    spin33,
    spin34,
    spin35,
    spin36,
    spin37,
    spin38,
    spin39,
    spin40,
    spin41,
    spin42,
    spin43,
    spin44,
    spin45,
    spin46,
    spin47,
    spin48,
    spin49,
    spin50,
    spin51,
    spin52,
    spin53,
    spin54,
    spin55,
    spin56,
    spin57,
    spin58,
    spin59,
    spin60,
    spin61,
    spin62,
    spin63,
    spin64,
    spin65,
    spin66,
    spin67,
    spin68,
    spin69,
    spin70,
    spin71,
]
