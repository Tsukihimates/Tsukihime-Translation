; fix buggy line-feed
0xc5a18
mov x0, x9
end

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

;; kerning patch
0x13bde8
;; is current car 'I'?
cmp w26, #0x49
b.ne #0x14

;; load offset for next bytes
;; x0 is loaded into 2 instructions after patch
;; so can be safely used as scratch.
adrp x0, #0x19af000
add x0, x0, #0xda8

;; peek first byte of strign
ldrb w13, [x0]

;; is peek'd char "'"
;; TODO: why 0x29 and not 0x27?
cmp w13, #0x29
b.ne #0x08

;; apply kerning value
fmov s8, #5.0
nop
end

;; install post trampoline for next_char_as_utf32
0x13deb0
b #0x62f8
end

;; save the relevant bytes from the string into memory
;; x27 has a lingering reference to the string pointer.
0x1441a8
;; capture next character
;; lingering reference in x27
;; x27 can also sometimes be NULL or 0x1, so account for that
cmp x27, #0x10000
b.lt #0x08
ldrb w13, [x27, #0x01]

;; store captured character
adrp x1, #0x19af000
add x1, x1, #0xda8
strb w13, [x1]

;; restore sp (overridden instruction)
add sp, sp, #0x20
ret
end
