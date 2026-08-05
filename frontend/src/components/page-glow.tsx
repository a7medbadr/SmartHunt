// The same subtle decorative glow behind the Dashboard's header, reused
// across every page per explicit request ("نثبت نفس الشكل ده في بقية
// التابات"). Purely decorative and absolutely positioned, so it never
// affects layout/scroll height — drop it as the first child inside a
// `relative overflow-hidden` wrapper.
export function PageGlow() {
  return (
    <>
      <div
        aria-hidden
        className="pointer-events-none absolute -top-24 -right-24 -z-10 size-[28rem] rounded-full bg-primary/20 blur-3xl"
      />
      <div
        aria-hidden
        className="pointer-events-none absolute -top-10 left-1/3 -z-10 size-72 rounded-full bg-fuchsia-500/10 blur-3xl"
      />
    </>
  );
}
