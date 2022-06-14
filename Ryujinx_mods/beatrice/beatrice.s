; cancel full-width extra spacing between lines.
0xc05cc
nop
end

; stop line feed
0xc5a24
b #0x4b4
end

; install trampoline
0xbe86c
call #0xc4dd8
; skip old check logic
cmp w8, #0x00
beq #0x1fc
end

; utf32 in w0
; result in w8 (gets overwritten by ldr immediately)
; 0x00 is mode 0, 0x01 is mode 1.
; sure hope this code is as unused as it seems!
0xc4dd8
cmp w0, #0x100
bgt #0x0C
; ascii
mov w8, #0x01
ret

cmp w0, #0xE000
blt #0x14
cmp w0, #0xF000
bgt #0x0C

mov w8, #0x01
ret
mov w8, #0x00
ret

end

; Enable recording video
0xfbf54
jump #0x153920
end

; Enable taking screenshots
0xfbf68
jump #0x153940
end
