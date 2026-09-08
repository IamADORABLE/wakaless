import { useEffect, useRef } from "react";

/** Six individual digit boxes (like a bank/telco OTP screen) instead of one
 * plain text field. Typing advances focus automatically; backspace on an
 * empty box steps back; pasting a full code fills every box at once. */
export default function OtpInput({ value, onChange, length = 6, autoFocus = true }) {
  const inputsRef = useRef([]);
  const digits = Array.from({ length }, (_, i) => value[i] || "");

  useEffect(() => {
    if (autoFocus) inputsRef.current[0]?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function setDigitAt(index, digit) {
    const next = digits.slice();
    next[index] = digit;
    onChange(next.join(""));
  }

  function handleChange(index, e) {
    const raw = e.target.value.replace(/\D/g, "");
    if (!raw) {
      setDigitAt(index, "");
      return;
    }
    // Handles a fast typist whose keystroke briefly lands more than one
    // character in a box, not just paste (paste is handled separately below).
    const chars = raw.split("");
    const next = digits.slice();
    let i = index;
    for (const ch of chars) {
      if (i >= length) break;
      next[i] = ch;
      i += 1;
    }
    onChange(next.join(""));
    inputsRef.current[Math.min(i, length - 1)]?.focus();
  }

  function handleKeyDown(index, e) {
    if (e.key === "Backspace" && !digits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
      setDigitAt(index - 1, "");
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputsRef.current[index - 1]?.focus();
    } else if (e.key === "ArrowRight" && index < length - 1) {
      inputsRef.current[index + 1]?.focus();
    }
  }

  function handleFocus(e) {
    // A box that already has a digit is at its native maxLength, so typing
    // over it does nothing unless the existing digit is selected first.
    e.target.select();
  }

  function handlePaste(e) {
    e.preventDefault();
    const pasted = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length);
    if (!pasted) return;
    onChange(pasted);
    inputsRef.current[Math.min(pasted.length, length - 1)]?.focus();
  }

  return (
    <div style={{ display: "flex", gap: 10 }} onPaste={handlePaste}>
      {digits.map((digit, i) => (
        <input
          key={i}
          ref={(el) => { inputsRef.current[i] = el; }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(i, e)}
          onKeyDown={(e) => handleKeyDown(i, e)}
          onFocus={handleFocus}
          onClick={handleFocus}
          aria-label={`Digit ${i + 1}`}
          style={{
            width: 48, height: 56, textAlign: "center", fontSize: 22, fontWeight: 700,
            border: `1.5px solid ${digit ? "var(--teal)" : "var(--border)"}`,
            borderRadius: 10, background: "var(--white)", color: "var(--ink)",
          }}
        />
      ))}
    </div>
  );
}
