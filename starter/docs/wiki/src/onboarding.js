/**
 * Onboarding: six mooring posts along a canal, one for each stage an
 * Alappuzha operator passes through — dm, form, review, approve, boats,
 * live. The pointer picks a post; it rises and brightens, its neighbours
 * rise a little less, staggered outward, and the boat glides over to moor
 * at it. The read-out names the stage.
 *
 * The pattern: discrete items like riffle — tweens, a stagger by distance,
 * identity by position, and a hit test on rest heights only.
 */
const {
  Cam, facing, fit, proj, rings, prism, seg,
  tdone, tset, tval, tween, disposer, mk, pointer, reflect, register,
} = HL;

const STAGES = ["dm", "form", "review", "approve", "boats", "live"];
const N = 6;
const REST = [0.4, 1.8, 0.8, 2.2, 1.1, 0.6];   // rest rise per post — the dune
const LIFT = 4.4, STEP = 1.8;                  // picked post rises LIFT, falloff STEP/edge
const PW = 7, PH = 12, PY = 3;                 // post footprint y PY..PY+PW on the water
const WX0 = -6, WX1 = 132, WY0 = 0, WY1 = 34, WZ = 2;   // canal slab
const HW = 16, HD = 7, HY = 14, HZ0 = WZ, HZ1 = WZ + 2.6; // boat hull
const CW = 8, CD = 5, CZ1 = HZ1 + 3.2;         // cabin, centred on the hull
const PX = (i) => 6 + i * 21;                  // post i footprint x PX..PX+PW

const postTopX = (i) => PX(i) + PW / 2;
const boatX = (a) => postTopX(a) - HW / 2;

function mount({ stage, svg, read }, value) {
  const bag = disposer();
  let stag = value;

  const C = Cam(45, 0.5, 1.9);
  fit(C, [[WX0, WY0, 0], [WX1, WY1, 0], [WX0, WY0, WZ + PH + LIFT + 2.2],
          [WX1, WY0, WZ + PH], [WX1, WY1, CZ1]], 200, 166);
  const P = proj(C), front = facing(C);

  const g = mk("g", {}, svg);

  // canal: one opaque water slab; the dashed route lies on it, posts and boat on top.
  const water = (() => {
    const [ring, inner] = rings(WX0, WY0, WX1, WY1, 5, 1.4);
    const s = mk("g", {}, g);
    const sl = mk("path", {}, s), cr = mk("path", { class: "lo" }, s);
    const q = prism(P, front, ring, inner, 0, WZ);
    sl.setAttribute("d", q.sil); sl.setAttribute("class", "sil");
    cr.setAttribute("d", q.crease);
    return s;
  })();
  reflect(svg, g, P, front, rings(WX0, WY0, WX1, WY1, 5, 1.4)[0], 0, 12);

  mk("path", { class: "nf dash",
    d: seg(P(-2, HY + HD / 2, WZ + 0.15), P(WX1 + 2, HY + HD / 2, WZ + 0.15)) }, g);

  const posts = [];
  for (let i = 0; i < N; i++) {
    const [ring, inner] = rings(PX(i), PY, PX(i) + PW, PY + PW, 2.4, 1.3);
    const grp = mk("g", {}, g);
    const sil = mk("path", { class: "sil" }, grp), cr = mk("path", { class: "lo" }, grp);
    posts.push({ ring, inner, sil, cr, h: tween(REST[i]), last: null });
  }

  const hullRing = (bx) => rings(bx, HY, bx + HW, HY + HD, 3, 1.2);
  const cabRing = (bx) => rings(bx + (HW - CW) / 2, HY + (HD - CD) / 2, bx + (HW + CW) / 2, HY + (HD + CD) / 2, 1.8, 1);
  const boat = {
    hull: mk("g", {}, g), cab: mk("g", {}, g), x: tween(boatX(0)),
    lastX: null,
    hullSil: mk("path", { class: "sil hi" }), hullCr: mk("path", { class: "lo" }),
    cabSil: mk("path", { class: "sil" }), cabCr: mk("path", { class: "lo" }),
  };
  boat.hull.append(boat.hullSil, boat.hullCr);
  boat.cab.append(boat.cabSil, boat.cabCr);

  // rest-top centres: the hit test reads these only, so a rising post never flickers.
  const tops = posts.map((_, i) => P(postTopX(i), PY + PW / 2, WZ + PH + REST[i])[0]);

  function draw() {
    const now = performance.now();
    const bx = tval(boat.x, now);
    if (bx !== boat.lastX) {
      boat.lastX = bx;
      const [hr, hi] = hullRing(bx), [cr, ci] = cabRing(bx);
      let q = prism(P, front, hr, hi, HZ0, HZ1);
      boat.hullSil.setAttribute("d", q.sil); boat.hullCr.setAttribute("d", q.crease);
      q = prism(P, front, cr, ci, HZ1, CZ1);
      boat.cabSil.setAttribute("d", q.sil); boat.cabCr.setAttribute("d", q.crease);
    }
    posts.forEach((p) => {
      const h = tval(p.h, now);
      if (h === p.last) return;
      p.last = h;
      const q = prism(P, front, p.ring, p.inner, WZ, WZ + PH + h);
      p.sil.setAttribute("d", q.sil); p.cr.setAttribute("d", q.crease);
    });
  }

  const B = register(stage, (_dt, now) => {
    draw();
    return !tdone(boat.x, now) || posts.some((p) => !tdone(p.h, now));
  });
  bag.add(B.unregister);

  let act = -1;
  function setActive(a) {
    if (a === act) return;
    const now = performance.now(), from = a >= 0 ? a : act;
    act = a;
    posts.forEach((p, i) => {
      const rise = a < 0 ? 0 : Math.max(0, LIFT - Math.abs(i - a) * STEP);
      tset(p.h, REST[i] + rise, now, Math.abs(i - from) * stag);
      p.sil.classList.toggle("hi", i === a);
    });
    boat.hullSil.classList.toggle("hi", a < 0);
    if (a >= 0) tset(boat.x, boatX(a), now, 0);
    else tset(boat.x, boatX(0), now, 0);
    read.textContent = a < 0 ? "rest" : `0${a + 1} ${STAGES[a]}`;
    B.wake();
  }

  const hit = ([x]) => {
    let best = -1, bd = Infinity;
    tops.forEach((tx, i) => { const d = Math.abs(x - tx); if (d < bd) { bd = d; best = i; } });
    return bd < 26 ? best : -1;
  };

  bag.add(pointer(stage, { move: (p) => setActive(hit(p)), leave: () => setActive(-1) }));
  bag.add(() => svg.replaceChildren());
  draw();

  return { set: (v) => { stag = v; }, destroy: bag.dispose };
}

hairline({
  name: "onboarding",
  means: "Six mooring posts, one per onboarding stage: the pointer's post rises, and the boat glides over to moor at it.",
  rules: [1, 2, 4, 5],
  range: [0, 40, 90],
  tour: [[119, 116], [148, 128], [176, 144], [204, 156], [232, 172], [260, 186]],
  mount,
});
