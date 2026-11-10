#!/usr/bin/env python3
"""Exercise the actual optional firmware input recorder without USB hardware."""
import json
import os
import struct
import subprocess
from build_studio import GAME, ROOT, engine_inputs


def main():
    work = GAME / 'out/trace-protocol'
    work.mkdir(parents=True, exist_ok=True)
    flags, sources, _ = engine_inputs(work)
    # Only the host Serial output sink changes; the actual sketch, input
    # sampling, protocol, frame loop and gameplay sources are compiled as-is.
    platform = work / 'platform.cpp'
    code = (GAME / 'tools/wasm/platform.cpp').read_text()
    code = '#include <cstdio>\n' + code
    code = code.replace('size_t SimSerial::write(uint8_t){return 1;}',
                        'size_t SimSerial::write(uint8_t c){return fwrite(&c,1,1,stdout);}')
    code = code.replace('size_t SimSerial::write(const uint8_t *,size_t n){return n;}',
                        'size_t SimSerial::write(const uint8_t *p,size_t n){return fwrite(p,1,n,stdout);}')
    platform.write_text(code)
    driver = work / 'probe.cpp'
    driver.write_text(r'''#include <CHGame.h>
#include "Live.h"
extern "C" {void pb_init();void pb_step(unsigned);}
int main(){
 pb_init();pinball::live::command("Y 12345");
 const unsigned masks[]={16,16,18,0,0,2};for(unsigned mask:masks)pb_step(mask);
 pinball::live::command("Y 1");pinball::live::command("Q 1");
 for(unsigned n=0;n<4;++n)pb_step(0);
 pinball::live::command("Y 1");pinball::live::command("R 999");
 pinball::live::command("P 60,160");pinball::live::command("Q 0");
 for(unsigned n=0;n<80;++n)pb_step(n&1?16:2);
 pinball::live::command("Y 1");pinball::live::command("Y 0");
 for(unsigned n=0;n<8;++n)pb_step(0);
 pinball::live::command("Y 1");
}
''')
    sources = [platform if s == GAME / 'tools/wasm/platform.cpp' else s for s in sources]
    exe = work / 'probe'
    subprocess.run([os.environ.get('CXX', 'clang++'), *flags, *sources, driver, '-o', exe], check=True, cwd=ROOT)
    output = subprocess.check_output([exe], text=True, cwd=ROOT).splitlines()
    assert output[-1] == 'LIVE ERR', output
    packets = [bytes.fromhex(line.removeprefix('LIVE DATA ')) for line in output[:-1]]
    assert len(packets) == 9
    frames = [struct.unpack_from('<I', data)[0] for data in packets]
    assert frames == [0, 6, 6, 10, 10, 10, 10, 90, 90], frames
    builds = [struct.unpack_from('<I', data, 4)[0] for data in packets]
    assert builds[0] and len(set(builds)) == 1
    def expand(data):
        return [data[i] for i in range(9, len(data), 2) for _ in range(data[i + 1])]
    assert expand(packets[1]) == [16, 16, 18, 0, 0, 2]
    assert expand(packets[3]) == [0] * 4, 'pause must not stop the input sequence'
    assert all(data[8] == 0 for data in packets[:7])
    assert packets[7][8] & 1, 'overflow must be explicit rather than losing ticks silently'
    assert len(packets[7]) == 9 + 64, 'recorder must remain bounded'
    report = dict(result='passed', wire_packets=len(packets), frames=frames,
                  sampled_masks_exact=True, paused_frames_included=True,
                  mutation_barriers=True, explicit_bounded_overflow=True, stop_disables_recording=True,
                  build=builds[0])
    (work / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
