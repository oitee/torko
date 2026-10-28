import React, { useEffect, useRef } from "react";
import "./Popover.css";

// The Popover component renders a floating sheet or panel.
// It closes on Escape or outside click, and returns focus to the trigger.
export default function Popover({
  open = false,
  onClose,
  triggerRef,
  anchorRef,
  children,
  className = "",
  role,
  id,
  style,
  ...rest
}) {
  const popoverRef = useRef(null);
  const effectiveTrigger = triggerRef || anchorRef;
  const prevOpenRef = useRef(open);

  const getTriggerElement = () => {
    if (!effectiveTrigger) return null;
    return effectiveTrigger.current || (effectiveTrigger instanceof HTMLElement ? effectiveTrigger : null);
  };

  useEffect(() => {
    if (prevOpenRef.current && !open) {
      const el = getTriggerElement();
      el?.focus?.();
    }
    prevOpenRef.current = open;
  }, [open, effectiveTrigger]);

  useEffect(() => {
    if (!open) {
      return;
    }

    function handleKeyDown(event) {
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        onClose?.();
        const el = getTriggerElement();
        el?.focus?.();
      }
    }

    function handleMouseDown(event) {
      const popoverEl = popoverRef.current;
      const triggerEl = getTriggerElement();
      if (popoverEl && !popoverEl.contains(event.target)) {
        if (triggerEl && triggerEl.contains(event.target)) {
          return;
        }
        onClose?.();
        triggerEl?.focus?.();
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleMouseDown);

    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleMouseDown);
    };
  }, [open, onClose, effectiveTrigger]);

  if (!open) {
    return null;
  }

  const combinedClassName = ["popover", className].filter(Boolean).join(" ");

  return (
    <div
      ref={popoverRef}
      className={combinedClassName}
      role={role}
      id={id}
      style={style}
      {...rest}
    >
      {children}
    </div>
  );
}

export { Popover };
