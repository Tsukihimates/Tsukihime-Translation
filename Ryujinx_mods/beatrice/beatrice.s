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
; U+2661 is the heart that noel uses.
mov w8, #0x2661
cmp w0, w8
beq #0x0C

mov w8, #0x01
ret
mov w8, #0x00
ret
end

; Enable recording video
0xfbf54
call #0x153920
end

; Enable taking screenshots
0xfbf68
call #0x153940
end
