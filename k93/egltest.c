/* egltest -- what Hyprland does: GBM on a DRM node, then eglInitialize. */
#include <EGL/egl.h>
#include <EGL/eglext.h>
#include <fcntl.h>
#include <gbm.h>
#include <stdio.h>

int main(int argc, char **argv)
{
	const char *node = argc > 1 ? argv[1] : "/dev/dri/card0";
	int fd = open(node, O_RDWR | O_CLOEXEC);
	if (fd < 0) { perror(node); return 1; }
	struct gbm_device *gbm = gbm_create_device(fd);
	printf("gbm_create_device(%s): %p backend %s\n", node, (void *)gbm,
	       gbm ? gbm_device_get_backend_name(gbm) : "-");
	if (!gbm) return 1;
	PFNEGLGETPLATFORMDISPLAYEXTPROC gpd =
		(PFNEGLGETPLATFORMDISPLAYEXTPROC)eglGetProcAddress("eglGetPlatformDisplayEXT");
	EGLDisplay d = gpd(EGL_PLATFORM_GBM_KHR, gbm, NULL);
	EGLint maj, min;
	if (!eglInitialize(d, &maj, &min)) {
		printf("eglInitialize failed: 0x%x\n", eglGetError());
		return 1;
	}
	printf("EGL %d.%d %s\n", maj, min, eglQueryString(d, EGL_VENDOR));
	printf("%s\n", eglQueryString(d, EGL_EXTENSIONS));
	return 0;
}
