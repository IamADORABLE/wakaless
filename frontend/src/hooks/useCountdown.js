import { useEffect, useState } from "react";

/** Ticks `seconds` down to 0 once per second, restart with `restart()`
 * (e.g. right after sending/resending a code). */
export default function useCountdown(initialSeconds) {
  const [seconds, setSeconds] = useState(initialSeconds);

  useEffect(() => {
    if (seconds <= 0) return;
    const timer = setInterval(() => setSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(timer);
  }, [seconds]);

  function restart() {
    setSeconds(initialSeconds);
  }

  return { seconds, restart };
}
