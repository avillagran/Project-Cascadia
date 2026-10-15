#!/bin/sh
# tools/piglit/build.sh -- piglit, the OpenGL test suite, for the iPad
# (docs/research/p105-mesa.md, M35): the desktop GL and GLES 2 tests, run
# through waffle (surfaceless EGL, or GBM / X11 / Wayland).
#
# On the host:
#   git clone --depth 1 https://gitlab.freedesktop.org/mesa/piglit.git build/piglit-src
#   docker build --platform linux/arm/v7 -t cascadia-piglit tools/piglit
#   docker run --rm --platform linux/arm/v7 -v $PWD:/cascadia cascadia-piglit sh tools/piglit/build.sh
#   tar cf - -C build/piglit-install . | ssh root@10.55.0.2 'mkdir -p /root/piglit && tar xf - -C /root/piglit'
#
# On the iPad (a run of the GL 2.1 profile; see tools/piglit/run.sh):
#   PIGLIT_PLATFORM=surfaceless_egl /root/piglit/bin/piglit run quick_gl /root/piglit-results/NAME
set -eu
ROOT=/cascadia
SRC=$ROOT/build/piglit-src
B=$ROOT/build/piglit-build
I=$ROOT/build/piglit-install
[ -f "$SRC/CMakeLists.txt" ] || { echo "no piglit source in build/piglit-src" >&2; exit 1; }
if [ ! -f "$B/build.ninja" ]; then
    cmake -S "$SRC" -B "$B" -G Ninja -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX=/ \
        -DPIGLIT_BUILD_GL_TESTS=ON -DPIGLIT_BUILD_GLES1_TESTS=OFF \
        -DPIGLIT_BUILD_GLES2_TESTS=ON -DPIGLIT_BUILD_GLES3_TESTS=OFF \
        -DPIGLIT_BUILD_CL_TESTS=OFF -DPIGLIT_BUILD_VK_TESTS=OFF \
        -DPIGLIT_BUILD_DMA_BUF_TESTS=OFF -DPIGLIT_USE_WAFFLE=ON
fi
ninja -C "$B"
rm -rf "$I"
DESTDIR="$I" ninja -C "$B" install >/dev/null
echo "built: build/piglit-install"
