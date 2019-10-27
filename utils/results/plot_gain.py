from collections import namedtuple

import matplotlib.pyplot as plt

plt.rc('text', usetex=True)
plt.rc('font', family='sans-serif', size=13)
plt.rc('figure', facecolor='k')

samples = [1, 5, 10, 20, 30]

Perf = namedtuple('Perf', ('demand', 'means', 'std'))

colours = {900: 'darkorange', 1350: 'crimson', 1800: 'royalblue', 1200: 'crimson', 1500: 'royalblue',
           4000: 'royalblue', 5000: 'crimson', 6000: 'darkorange'}

linestyles = {900: ':', 1350: '--', 1800: '-', 1200: '--', 1500: '-',
           4000: ':', 5000: '--', 6000: '-'}

perf = { 'Isolated Intersection':
           { 'U-TuSeRACT vs U-SURTRAC': [
                Perf(demand='900 vehicles/hour',
                     means=[20.32,  -38.33, -44.62, -45.70, -45.16],
                     std=[18.99,  12.36,  9.40,   9.14,   10.46]),
                Perf(demand='1350 vehicles/hour',
                     means=[-10.09, -36.88, -39.87, -41.76, -31.30],
                     std=[15.79,  11.68,  11.69,  12.09,  22.40]),
                Perf(demand='1800 vehicles/hour',
                     means=[-29.24, -35.26, -36.75, -29.45, -17.29],
                     std=[10.36,  15.25,  17.08,  18.39,  20.19])
                ]
            },
        'Arterial Network':
            { 'U-TuSeRACT vs U-SURTRAC': [
                  Perf(demand='900 vehicles/hour',
                       means=[56.96, -21.97, -32.71, -38.03, -39.97],
                       std=[28.86, 17.16, 22.57, 19.58, 18.69]),
                  Perf(demand='1200 vehicles/hour',
                       means=[48.97, -27.21, -20.29, -24.81, -21.3],
                       std=[18.58, 16.37, 22.87, 18.05, 20.32]),
                  Perf(demand='1500 vehicles/hour',
                       means=[44.44, -18.41, -10.91, -10.36, -11.45],
                       std=[17.07, 13.62, 15.63, 14.46, 17.44])
                  ],
              'C-TuSeRACT vs C-SURTRAC': [
                  Perf(demand='900 vehicles/hour',
                       means=[59.39, -36.15, -42.17, -41.24, -38.27],
                       std=[28.85, 21.07, 19.11, 18.72, 19.54]),
                  Perf(demand='1200 vehicles/hour',
                       means=[37.43, -29.36, -30.58, -23.41, -16.5],
                       std=[15.82, 15.3, 16.04, 16.57, 16.7]),
                  Perf(demand='1500 vehicles/hour',
                       means=[21.74, -21.03, -19.12, -16.48, -11.69],
                       std=[15.13, 11.05, 11.92, 13.57, 13.47])
                  ],
              'C-TuSeRACT vs U-TuSeRACT': [
                  Perf(demand='900 vehicles/hour',
                       means=[2.54, -14.39, -8.27, 3.2, 11.0],
                       std=[13.08, 34.44, 34.31, 41.98, 44.36]),
                  Perf(demand='1200 vehicles/hour',
                       means=[-6.18, 2.62, -5.45, 8.62, 14.98],
                       std=[9.06, 31.33, 32.13, 35.28, 40.11]),
                  Perf(demand='1500 vehicles/hour',
                       means=[-14.37, 0.74, -5.45, -3.52, 4.37],
                       std=[7.81, 22.48, 20.62, 20.93, 24.96])
              ]
            },
        '5x5 Grid':
            { 'U-TuSeRACT vs U-SURTRAC': [
                  Perf(demand='4000 vehicles/hour',
                       means=[27.22, -13.16, -15.54, -17.06, -14.81],
                       std=[14.83, 8.28, 9.26, 9.43, 10.02]),
                  Perf(demand='5000 vehicles/hour',
                       means=[23.25, -18.32, -12.6, -11.2, -8.51],
                       std=[13.66, 8.35, 11.23, 11.67, 12.07]),
                  Perf(demand='6000 vehicles/hour',
                       means=[24.47, -12.39, -4.14, -3.4, 2.98],
                       std=[13.01, 8.65, 8.84, 9.79, 10.62])
              ],
              'C-TuSeRACT vs C-SURTRAC': [
                  Perf(demand='4000 vehicles/hour',
                       means=[32.09, -26.59, -40.88, -42.92, -41.69],
                       std=[13.0, 5.25, 6.54, 5.56, 7.36]),
                  Perf(demand='5000 vehicles/hour',
                       means=[29.92, -24.85, -31.68, -27.57, -25.72],
                       std=[10.29, 7.9, 7.54, 9.74, 10.48]),
                  Perf(demand='6000 vehicles/hour',
                       means=[20.64, -22.64, -20.54, -15.0, -8.81],
                       std=[10.93, 8.18, 9.45, 10.71, 12.76])
              ],
              'C-TuSeRACT vs U-TuSeRACT': [
                  Perf(demand='4000 vehicles/hour',
                       means=[-4.98, -22.86, -36.12, -36.95, -37.33],
                       std=[11.45, 7.16, 7.29, 8.03, 9.15]),
                  Perf(demand='5000 vehicles/hour',
                       means=[-6.08, -18.36, -30.13, -27.21, -27.4],
                       std=[10.57, 9.23, 10.52, 11.47, 12.84]),
                  Perf(demand='6000 vehicles/hour',
                       means=[-9.63, -17.75, -22.83, -17.89, -17.4],
                       std=[10.15, 9.76, 10.82, 12.15, 12.6])
              ]
            },
        }

for network, values in perf.items():
    for comparison, performances in values.items():
        print('============')
        for performance in performances:
            print(performance.demand)
            plt.errorbar(samples, performance.means, yerr=performance.std, color=colours[float(performance.demand.split()[0])],
              linestyle=linestyles[float(performance.demand.split()[0])], capsize=3, alpha=0.5, lolims=True, uplims=True,
              label=performance.demand)

        plt.xlabel('Sample count')
        plt.ylabel('Change in mean waiting time relative to {} (\%)'.format(comparison.split()[-1]))
        # plt.title('{}: {}'.format(network, comparison))
        plt.legend(fontsize='x-small')

        plt.show()

        # with open('{}-{}.png'.format(network.split()[0].lower(), comparison.lower().replace(' ', '-')), 'w') as fp:
        #     plt.savefig(fp, dpi=300)

        plt.clf()


