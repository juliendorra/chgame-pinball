// Integer contact-friction invariants, independent of renderer and PRNG.
#include "Spin.h"
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
using namespace pinball;
static void require(bool ok,const char *why){if(!ok){std::fprintf(stderr,"FAIL %s\n",why);std::exit(1);}}
static double energy(int32_t x,int32_t y,int32_t spin){return double(x)*x+double(y)*y+.4*double(spin/256.0)*(spin/256.0);}
int main(){
    unsigned count=0;double worstGain=0;
    for(unsigned grip:{16u,32u,64u})for(int angle=0;angle<360;angle+=3)
    for(int tangent:{-1200,-300,0,300,1200})for(int spin0:{-900,0,900}) {
        double a=angle*3.141592653589793/180;
        int nx=int(std::cos(a)*256),ny=int(std::sin(a)*256);
        int32_t x=-ny*tangent/256,y=nx*tangent/256,spin=spin0*256;
        int32_t mx=-x,my=y,ms=-spin;
        double before=energy(x,y,spin);
        int oldSlip=(x*-ny+y*nx)/256-spin/256;
        int impulse=spinContact(x,y,spin,nx,ny,900,grip);
        spinContact(mx,my,ms,-nx,ny,900,grip);
        require(mx==-x && my==y && ms==-spin,"mirror symmetry");
        require(std::abs(impulse)<=900*int(grip)/256,"Coulomb limit");
        int newSlip=(x*-ny+y*nx)/256-spin/256;
        require(std::abs(newSlip)<=std::abs(oldSlip)+1,"slip reduction");
        double gain=energy(x,y,spin)-before;if(gain>worstGain)worstGain=gain;
        require(gain<=0.0001,"stationary contact must not create combined energy");
        ++count;
    }
    int32_t x=0,y=-400,spin=256*400;
    spinContact(x,y,spin,0,256,900,32);
    require(x<0 && spin<256*400,"stored spin changes next rebound");
    int32_t xx=x,yy=y,ss=spin;spinContact(x,y,spin,0,256,900,0);
    require(x==xx && y==yy && spin==ss,"disabled model exact identity");
    x=400;y=-400;spin=-400*256;spinContact(x,y,spin,0,256,900,32);
    require(x==400 && spin==-400*256,"rolling contact has no slip impulse");
    x=y=spin=0;spinContact(x,y,spin,256,0,900,32,0,-600);
    require(y<0 && spin>0,"moving surface transfers energy and spin");
    uint32_t rng=0x5A17B411;auto next=[&](){rng^=rng<<13;rng^=rng>>17;rng^=rng<<5;return rng;};
    for(unsigned i=0;i<100000;++i) {
        int dx=int(next()%2049)-1024,dy=int(next()%2049)-1024;
        int dist=int(std::sqrt(dx*dx+dy*dy));if(!dist)continue;
        int nx=dx*256/dist,ny=dy*256/dist; // same truncated normals as solver
        int32_t x=int(next()%4001)-2000,y=int(next()%4001)-2000,spin=int(next()%768001)-384000;
        int surfaceY=int(next()%12001)-6000;
        int64_t before=spinEnergy(x,y-surfaceY,spin);
        spinContact(x,y,spin,nx,ny,next()%5000,16u<<(next()%3),0,surfaceY);
        require(spinEnergy(x,y-surfaceY,spin)<=before,"quantized energy in surface frame");
        ++count;
    }
    std::printf("PASS %u contacts: energy, mirror, slip, friction limit; history, moving bat and disabled identity (max energy gain %.6f)\n",count,worstGain);
}
