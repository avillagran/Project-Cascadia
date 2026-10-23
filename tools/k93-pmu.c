/* pmu -- read or write the D1946 PMU (i2c-0, 0x3c) from Linux.
 *
 *   pmu dump                 registers 0x00..0x7f
 *   pmu r REG                one register
 *   pmu w REG MASK VAL       read-modify-write one register
 */
#include <fcntl.h>
#include <linux/i2c-dev.h>
#include <linux/i2c.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static int fd;

static int rd(int reg)
{
	unsigned char r = reg, v;
	struct i2c_msg m[2] = {
		{ .addr = 0x3c, .flags = 0, .len = 1, .buf = &r },
		{ .addr = 0x3c, .flags = I2C_M_RD, .len = 1, .buf = &v },
	};
	struct i2c_rdwr_ioctl_data x = { m, 2 };
	if (ioctl(fd, I2C_RDWR, &x) < 0)
		return -1;
	return v;
}

static int wr(int reg, int val)
{
	unsigned char b[2] = { reg, val };
	struct i2c_msg m = { .addr = 0x3c, .flags = 0, .len = 2, .buf = b };
	struct i2c_rdwr_ioctl_data x = { &m, 1 };
	return ioctl(fd, I2C_RDWR, &x);
}

int main(int argc, char **argv)
{
	fd = open("/dev/i2c-0", O_RDWR);
	if (fd < 0) { perror("/dev/i2c-0"); return 1; }
	if (argc >= 2 && !strcmp(argv[1], "dump")) {
		for (int r = 0; r < 0x80; r++)
			printf("%02x%s", rd(r) & 0xff, (r & 15) == 15 ? "\n" : " ");
		return 0;
	}
	if (argc == 3 && !strcmp(argv[1], "r")) {
		printf("%02x\n", rd(strtoul(argv[2], NULL, 16)));
		return 0;
	}
	if (argc == 5 && !strcmp(argv[1], "w")) {
		int reg = strtoul(argv[2], NULL, 16), mask = strtoul(argv[3], NULL, 16);
		int val = strtoul(argv[4], NULL, 16), old = rd(reg);
		if (old < 0) { perror("read"); return 1; }
		int nv = (old & ~mask) | (val & mask);
		if (wr(reg, nv) < 0) { perror("write"); return 1; }
		printf("%02x: %02x -> %02x\n", reg, old, rd(reg));
		return 0;
	}
	fprintf(stderr, "usage: pmu dump | r REG | w REG MASK VAL\n");
	return 2;
}
