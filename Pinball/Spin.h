#pragma once
#include <stdint.h>

// Standard model for firmware, Studio and isolated builds: light spin. Q8 friction
// coefficient: 16=1/16, 32=1/8, 64=1/4. Compare with benchmark_spin.py.
#ifndef PINBALL_SPIN_GRIP
#define PINBALL_SPIN_GRIP 16
#endif
#ifndef PINBALL_SPIN_FORGET
#define PINBALL_SPIN_FORGET 0
#endif
namespace pinball {
static_assert(PINBALL_SPIN_GRIP >= 0 && PINBALL_SPIN_GRIP <= 64, "Spin grip outside tested range");
inline int64_t spinEnergy(int32_t vx,int32_t vy,int32_t spin) {
    // Five times combined energy in common Q32 units; no floating point.
    return (int64_t(vx)*vx+int64_t(vy)*vy)*327680+int64_t(spin)*spin*2;
}
// spin stores omega*radius in Q16; translation and normals use Q8. Only
// rotation about the playfield normal is modelled (not 3-D rolling/topspin).
// For a solid sphere I=2/5*m*r^2, the impulse to remove slip is -2/7*slip.
// The Coulomb bound is mu*normalImpulse. This exchanges linear and rotational
// energy; it does not choose a random outgoing direction.
inline int spinContact(int32_t &vx, int32_t &vy, int32_t &spin,
                       int nx, int ny, int normalImpulse, unsigned grip,
                       int surfaceX=0, int surfaceY=0) {
    if (!grip || normalImpulse<=0) return 0;
    int32_t oldX=vx,oldY=vy,oldSpin=spin;
    int tx=-ny, ty=nx;
    int slip=((vx-surfaceX)*tx+(vy-surfaceY)*ty)/256-spin/256;
    int impulse=-slip*2/7, limit=normalImpulse*int(grip)/256;
    if(impulse < -limit)impulse=-limit;
    if(impulse > limit)impulse=limit;
    vx+=impulse*tx/256;vy+=impulse*ty/256;
    spin-=impulse*640; // delta(omega*r) = -5/2 * impulse, in Q16
    // Integer normals and rounded component impulses can otherwise add a
    // little energy near rolling contact. Reject that impulse. Measure in the
    // surface frame so a moving bat can still do work on the ball.
    // Algebraic energy difference / 2560: fewer wide multiplies than two
    // absolute-energy evaluations, with exactly the same integer decision.
    int dx=vx-oldX,dy=vy-oldY;
    int64_t change=(int64_t(dx)*(2*(oldX-surfaceX)+dx)+
                    int64_t(dy)*(2*(oldY-surfaceY)+dy))*128-
                   int64_t(oldSpin)*impulse+int64_t(impulse)*impulse*320;
    if(change>0) {
        vx=oldX;vy=oldY;spin=oldSpin;return 0;
    }
    return impulse;
}
}
