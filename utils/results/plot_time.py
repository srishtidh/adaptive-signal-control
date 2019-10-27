import matplotlib.pyplot as plt

plt.rc('text', usetex=True)
plt.rc('font', family='sans-serif', size=13)

figure, axes = plt.subplots(1, 3, sharex='all', sharey='all', figsize=(15, 5))

for ax in axes:
    plt.setp(ax.get_yticklabels(), visible=True)

plt.subplots_adjust(wspace=0.04)

samples = [1, 5,10, 20, 30]

t30_mean = [14.46, -34.91, -46.23, -45.82, -44.43]
t30_std = [16.56, 9.29, 8.83, 7.86, 7.88]

t5_mean = [13.29, -36.15, -47.76, -42.88, -45.76]
t5_std = [14.94, 11.67, 8.82, 8.94, 9.36]


ax = axes[0]
ax.errorbar(samples, t5_mean, yerr=t5_std, color='royalblue', linestyle=':', capsize=3, lolims=True, uplims=True, alpha=0.5, label='Solver time limit = 5 seconds')
ax.errorbar(samples, t30_mean, yerr=t30_std, color='crimson', linestyle='--', capsize=3, lolims=True, uplims=True, alpha=0.5,label='Solver time limit = 30 seconds')
ax.set_xlabel('Sample count')
ax.set_ylabel('Change in mean waiting time relative to U-SURTRAC (\%)')
ax.set_title('900 vehicles / hour')
ax.legend()

t30_mean = [-8.40, -41.71, -43.06, -40.82, -39.13]
t30_std = [16.98, 10.84, 13.43, 14.92, 10.12]

t5_mean = [-9.29, -39.32, -37.84, -41.85, -29.76]
t5_std = [20.10, 11.21, 15.10, 12.13, 24.65]

ax = axes[1]
ax.errorbar(samples, t5_mean, yerr=t5_std, color='royalblue', linestyle=':', capsize=3, lolims=True, uplims=True, alpha=0.5, label='Solver time limit = 5 seconds')
ax.errorbar(samples, t30_mean, yerr=t30_std, color='crimson', linestyle='--', capsize=3, lolims=True, uplims=True, alpha=0.5,label='Solver time limit = 30 seconds')
ax.set_xlabel('Sample count')
# ax.set_ylabel('Change in mean waiting time with respect to U-SURTRAC (\%)')
ax.set_title('1350 vehicles / hour')
ax.set_facecolor('darkgrey')
ax.legend()

t30_mean = [-30.57, -42.07, -38.12, -40.66, -38.59]
t30_std = [10.63, 10.07, 13.66, 12.07, 12.67]

t5_mean = [-31.46, -38.08, -35.31, -31.45, -16.38]
t5_std = [9.70, 13.88, 16.18, 18.79, 19.24]

ax = axes[2]
ax.errorbar(samples, t5_mean, yerr=t5_std, color='royalblue', linestyle=':', capsize=3, lolims=True, uplims=True, alpha=0.5, label='Solver time limit = 5 seconds')
ax.errorbar(samples, t30_mean, yerr=t30_std, color='crimson', linestyle='--', capsize=3, lolims=True, uplims=True, alpha=0.5,label='Solver time limit = 30 seconds')
ax.set_xlabel('Sample count')
# ax.set_ylabel('Change in mean waiting time with respect to U-SURTRAC (\%)')
ax.set_title('1800 vehicles / hour')
ax.set_facecolor('k')
ax.legend()

# plt.show()

with open('timelimit.png', 'w') as fp:
    plt.savefig(fp, dpi=300)


