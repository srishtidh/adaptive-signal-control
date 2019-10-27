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
t30_yerr_llim = [t30_mean[ind] - t30_std[ind] for ind in range(len(t30_mean))]
t30_yerr_ulim = [t30_mean[ind] + t30_std[ind] for ind in range(len(t30_mean))]

t5_mean = [13.29, -36.15, -47.76, -42.88, -45.76]
t5_std = [14.94, 11.67, 8.82, 8.94, 9.36]
t5_yerr_llim = [t5_mean[ind] - t5_std[ind] for ind in range(len(t5_mean))]
t5_yerr_ulim = [t5_mean[ind] + t5_std[ind] for ind in range(len(t5_mean))]

ax = axes[0]
ax.plot(samples, t5_mean, color='royalblue', linestyle=':', alpha=0.5, label='Solver time limit = 5 seconds')
ax.fill_between(samples, t5_yerr_llim, t5_yerr_ulim, alpha=0.2)
ax.plot(samples, t30_mean, color='crimson', linestyle='--', alpha=0.5,label='Solver time limit = 30 seconds')
ax.fill_between(samples, t30_yerr_llim, t30_yerr_ulim, alpha=0.2)
ax.set_xlabel('Sample count')
ax.set_ylabel('Change in mean waiting time relative to U-SURTRAC (\%)')
ax.set_title('900 vehicles / hour')
ax.legend()

t30_mean = [-8.40, -41.71, -43.06, -40.82, -39.13]
t30_std = [16.98, 10.84, 13.43, 14.92, 10.12]
t30_yerr_llim = [t30_mean[ind] - t30_std[ind] for ind in range(len(t30_mean))]
t30_yerr_ulim = [t30_mean[ind] + t30_std[ind] for ind in range(len(t30_mean))]

t5_mean = [-9.29, -39.32, -37.84, -41.85, -29.76]
t5_std = [20.10, 11.21, 15.10, 12.13, 24.65]
t5_yerr_llim = [t5_mean[ind] - t5_std[ind] for ind in range(len(t5_mean))]
t5_yerr_ulim = [t5_mean[ind] + t5_std[ind] for ind in range(len(t5_mean))]

ax = axes[1]
ax.plot(samples, t5_mean, color='royalblue', linestyle=':', alpha=0.5, label='Solver time limit = 5 seconds')
ax.fill_between(samples, t5_yerr_llim, t5_yerr_ulim, alpha=0.2)
ax.plot(samples, t30_mean, color='crimson', linestyle='--', alpha=0.5,label='Solver time limit = 30 seconds')
ax.fill_between(samples, t30_yerr_llim, t30_yerr_ulim, alpha=0.2)
ax.set_xlabel('Sample count')
# ax.set_ylabel('Change in mean waiting time with respect to U-SURTRAC (\%)')
ax.set_title('1350 vehicles / hour')
# ax.set_facecolor('darkgrey')
ax.legend()

t30_mean = [-30.57, -42.07, -38.12, -40.66, -38.59]
t30_std = [10.63, 10.07, 13.66, 12.07, 12.67]
t30_yerr_llim = [t30_mean[ind] - t30_std[ind] for ind in range(len(t30_mean))]
t30_yerr_ulim = [t30_mean[ind] + t30_std[ind] for ind in range(len(t30_mean))]

t5_mean = [-31.46, -38.08, -35.31, -31.45, -16.38]
t5_std = [9.70, 13.88, 16.18, 18.79, 19.24]
t5_yerr_llim = [t5_mean[ind] - t5_std[ind] for ind in range(len(t5_mean))]
t5_yerr_ulim = [t5_mean[ind] + t5_std[ind] for ind in range(len(t5_mean))]

ax = axes[2]
ax.plot(samples, t5_mean, color='royalblue', linestyle=':', alpha=0.5, label='Solver time limit = 5 seconds')
ax.fill_between(samples, t5_yerr_llim, t5_yerr_ulim, alpha=0.2)
ax.plot(samples, t30_mean, color='crimson', linestyle='--', alpha=0.5,label='Solver time limit = 30 seconds')
ax.fill_between(samples, t30_yerr_llim, t30_yerr_ulim, alpha=0.2)
ax.set_xlabel('Sample count')
# ax.set_ylabel('Change in mean waiting time with respect to U-SURTRAC (\%)')
ax.set_title('1800 vehicles / hour')
# ax.set_facecolor('k')
ax.legend()

plt.show()

# with open('timelimit3.png', 'w') as fp:
#     plt.savefig(fp, dpi=300)


