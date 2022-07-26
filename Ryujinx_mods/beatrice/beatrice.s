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
;; is current char 'I'?
cmp w26, #0x49
b.ne #0x1c

;; load offset for next bytes
;; x0 is loaded into 2 instructions after patch
;; so can be safely used as scratch.
adrp x0, #0x19f8000
add x0, x0, #0x7c7

;; peek first byte of strign
ldrb w13, [x0]

;; is peek'd char "'"
cmp w13, #0x27
b.ne #0x08

;; apply kerning value
fmov s8, #5.0
nop
end

;; install trampoline for capturing next character
0x146374
;; jumps to 0x1441a8 (save link for tail-call)
bl #-0x21CC
end

;; save the relevant bytes from the string into memory
;; x0 has string pointer (immutable)
;; w13 seems safe as scratch TODO: true?
;; x1 immediately overwritten, save as scratch.
0x1441a8
;; capture next character
;; string pointer in x0
ldrb w13, [x0, #0x01]

;; store captured character
adrp x1, #0x19f8000
add x1, x1, #0x7c7
strb w13, [x1]

;; replace original call (no link)
br x8
end
