0x13bdcc
;; The value of this float constant
;; will be squared to determine the character advance.
fmov s8, #0x12
end

0x13be20
;; This actually applies the character advance
fmadd s0, s8, s8, s0
end

;; Cancel early line wrap.
0xc37f8
nop
end
