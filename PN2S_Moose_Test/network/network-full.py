import sys
import os
os.environ['MAX_DEVICE_NUMBER'] = '1'
import pylab
import numpy
import math
import time
from numpy import random as nprand, where
import csv
import moose
import moose.utils

EREST_ACT = -70e-3

# Gate equations have the form:
#
# y(x) = (A + B * x) / (C + exp((x + D) / F))

# where x is membrane voltage and y is the rate constant for gate
# closing or opening

Na_m_params = [1e5 * (25e-3 + EREST_ACT),   # 'A_A':
               -1e5,                       # 'A_B':
               -1.0,                       # 'A_C':
               -25e-3 - EREST_ACT,         # 'A_D':
               -10e-3,                      # 'A_F':
               4e3,                     # 'B_A':
               0.0,                        # 'B_B':
               0.0,                        # 'B_C':
               0.0 - EREST_ACT,            # 'B_D':
               18e-3                       # 'B_F':
               ]
Na_h_params = [70.0,                        # 'A_A':
               0.0,                       # 'A_B':
               0.0,                       # 'A_C':
               0.0 - EREST_ACT,           # 'A_D':
               0.02,                     # 'A_F':
               1000.0,                       # 'B_A':
               0.0,                       # 'B_B':
               1.0,                       # 'B_C':
               -30e-3 - EREST_ACT,        # 'B_D':
               -0.01                    # 'B_F':
               ]
K_n_params = [1e4 * (10e-3 + EREST_ACT),  # 'A_A':
              -1e4,  # 'A_B':
              -1.0,  # 'A_C':
              -10e-3 - EREST_ACT,  # 'A_D':
              -10e-3,  # 'A_F':
              0.125e3,  # 'B_A':
              0.0,  # 'B_B':
              0.0,  # 'B_C':
              0.0 - EREST_ACT,  # 'B_D':
              80e-3  # 'B_F':
              ]
VMIN = -30e-3 + EREST_ACT
VMAX = 120e-3 + EREST_ACT
VDIVS = 3000


def create_squid(parent):
    """Create a single compartment squid model."""
    soma = moose.SymCompartment(parent.path + '/soma')
    Em = EREST_ACT + 10.613e-3
    soma.Em = Em
    soma.initVm = EREST_ACT
    soma.Cm = 7.85e-9 * 0.5
    soma.Rm = 4.2e5 * 5.0
    soma.Ra = 7639.44e3

    nachan = moose.HHChannel(parent.path + '/soma/Na')
    nachan.Xpower = 3
    xGate = moose.HHGate(nachan.path + '/gateX')
    xGate.setupAlpha(Na_m_params + [VDIVS, VMIN, VMAX])
    # This is important: one can run without it but the output will diverge.
    xGate.useInterpolation = 1
    nachan.Ypower = 1
    yGate = moose.HHGate(nachan.path + '/gateY')
    yGate.setupAlpha(Na_h_params + [VDIVS, VMIN, VMAX])
    yGate.useInterpolation = 1
    nachan.Gbar = 0.942e-3
    nachan.Ek = 115e-3 + EREST_ACT
    moose.connect(nachan, 'channel', soma, 'channel', 'OneToOne')
    kchan = moose.HHChannel(parent.path + '/soma/K')
    kchan.Xpower = 4.0
    xGate = moose.HHGate(kchan.path + '/gateX')
    xGate.setupAlpha(K_n_params + [VDIVS, VMIN, VMAX])
    xGate.useInterpolation = 1
    kchan.Gbar = 0.2836e-3
    kchan.Ek = -12e-3 + EREST_ACT
    moose.connect(kchan, 'channel', soma, 'channel', 'OneToOne')
    return soma


def add_plot(objpath, field, plot):
    assert moose.exists(objpath)
    tab = moose.Table('/graphs/' + plot)
    obj = moose.element(objpath)
    moose.connect(tab, 'requestOut', obj, field)
    return tab


def dump_plots():
    pylab.figure(1)
    for x in moose.wildcardFind('/graphs/cpu/#[ISA=Table]'):
        t = numpy.arange(0, len(x.vector), 1)
        pylab.plot(t, x.vector, label=("CPU:%s" % x.name))
    for x in moose.wildcardFind('/graphs/gpu/#[ISA=Table]'):
        t = numpy.arange(0, len(x.vector), 1)
        pylab.plot(t, x.vector, label=("GPU:%s" % x.name))

    pylab.legend()
    pylab.show(block=False)
    
    pylab.figure(2)
    for x in moose.wildcardFind('/graphs/cpu/stat/#[ISA=Table]'):
        t = numpy.arange(0, len(x.vector), 1)
        pylab.plot(t, x.vector, label=("CPU:%s" % x.name))
        print "Mean:", x.vector[len(x.vector)-1]
    for x in moose.wildcardFind('/graphs/gpu/stat/#[ISA=Table]'):
        t = numpy.arange(0, len(x.vector), 1)
        pylab.plot(t, x.vector, label=("GPU:%s" % x.name))
        print "Mean:", x.vector[len(x.vector)-1]
    pylab.show()

def save_plots():
    cpufile = open("cpufile.csv", 'a')
    cpuwriter = csv.writer(cpufile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    first_line = True
    for x in moose.wildcardFind('/graphs/cpu/#[ISA=Table]'):
        if first_line:
            t = numpy.arange(0, len(x.vector), 1)
            cpuwriter.writerow(t)
            first_line = False
        cpuwriter.writerow(x.vector)
    
    gpufile = open("gpufile.csv", 'a')
    gpuwriter = csv.writer(gpufile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
    first_line = True
    for x in moose.wildcardFind('/graphs/gpu/#[ISA=Table]'):
        if first_line:
            t = numpy.arange(0, len(x.vector), 1)
            gpuwriter.writerow(t)
            first_line = False
        gpuwriter.writerow(x.vector)
    
    
def create_dendrit(name, parentCompt, parentObj, length, dia):
    RA = 1.0
    RM = 1.0
    CM = 0.01

    d = moose.SymCompartment(parentObj.path + '/' + name)
    moose.connect(parentCompt, 'distal', d, 'proximal', 'Single')
    d.diameter = dia
    d.length = length
    d.Ra = RA * length / (math.pi * d.diameter * d.diameter / 4.0)
    d.Rm = RM / (length * math.pi * d.diameter)
    d.Cm = CM * length * math.pi * d.diameter
    d.Em = EREST_ACT
    d.initVm = EREST_ACT

    return d


def make_spiny_compt(root_path, number, isExcitatory):
    comptLength = 200e-6
    comptDia = 4e-6

    if isExcitatory:
        name = root_path + "/cell" + str(number)
    else:
        name = root_path + "/cell_in" + str(number)
    cell = moose.Neutral(name)

    soma = create_squid(cell)
    soma.inject = INJECT_CURRENT
    soma.x0 = 0
    soma.y0 = 0
    soma.z0 = 0
    soma.x = comptLength
    soma.y = 0
    soma.z = 0
    soma.length = comptLength
    soma.diameter = comptDia

    # Create Dendrits
    spineLength = 150.0e-6
    spineDia = 20.0e-6
    d1 = create_dendrit('d1', soma, cell, spineLength, spineDia)
    d2 = create_dendrit('d2', d1, cell, spineLength, spineDia)
    d3 = create_dendrit('d3', d2, cell, spineLength, spineDia / 2)
    if isExcitatory:
        d4 = create_dendrit('d4', d2, cell, spineLength, spineDia/2)

    # Excitatory
    gluR_Ex = moose.SynChan(d3.path + '/gluR')
    gluR_Ex.tau1 = 4e-3
    gluR_Ex.tau2 = 4e-3
    gluR_Ex.Gbar = 1e-6
    gluR_Ex.Ek = 25.0e-3  
    moose.connect(d3, 'channel', gluR_Ex, 'channel', 'Single')
    synHandler = moose.SimpleSynHandler(d3.path + '/gluR/handler')
    synHandler.synapse.num = number_of_input_cells + number_of_ext_cells
    synHandler.synapse.vec.weight = 1.0 /10
    moose.connect(synHandler, 'activationOut', gluR_Ex, 'activation', 'Single')

    # Add Inhibitory characteristic
    if isExcitatory:
        gluR_In = moose.SynChan(d4.path + '/gluR')
        gluR_In.tau1 = 4e-3
        gluR_In.tau2 = 4e-3
        gluR_In.Gbar = 1e-6
        gluR_In.Ek = -20.0e-2  # Inhibitory -0.1
        moose.connect(d4, 'channel', gluR_In, 'channel', 'Single')
        synHandler = moose.SimpleSynHandler(d4.path + '/gluR/handler')
        if number_of_inh_cells > 0:
            synHandler.synapse.num = number_of_inh_cells
            synHandler.synapse.vec.weight = 1.0 /10
        moose.connect(synHandler, 'activationOut', gluR_In, 'activation', 'Single')

    return [cell, soma]


def create_cells(net, input_layer):
    network = moose.Neutral(net)

    # Create Ex cells
    for i in range(number_of_ext_cells):
        [cell, soma] = make_spiny_compt(network.path, i, True)
        spike = moose.SpikeGen(cell.path + '/spike')
        spike.refractT = 47e-3
        spike.threshold = 0
        spike.edgeTriggered = True
        spike.Vm(0)
        moose.connect(soma, 'VmOut', spike, 'Vm')
        #Record spike rate
        stats = moose.SpikeStats(cell.path + '/stat')
        stats.windowLength = 10
        moose.connect(spike, 'spikeOut', stats, 'addSpike')
    
        # Add Excitatory Connections
        rnd = nprand.rand(1, number_of_input_cells)
        indices = where(rnd <= IC)
        for j in indices[1]:
            syn = moose.element(cell.path + '/d3/gluR/handler')
            moose.connect(input_layer[j], 'spikeOut', syn.synapse[j], 'addSpike')
            syn.synapse[j].weight = 1.0/5
            syn.synapse[j].delay = 2e-3 + (8e-3 - 2e-3) * nprand.random_sample()  # random

            
    # Create Inh cells
    for i in range(number_of_inh_cells):
        [cell, soma] = make_spiny_compt(network.path, i, False)
        spike = moose.SpikeGen(cell.path + '/spike')
        spike.refractT = 47e-3
        spike.threshold = 0
        spike.edgeTriggered = True
        spike.Vm(0)
        moose.connect(soma, 'VmOut', spike, 'Vm')
        #Record spike rate
        stats = moose.SpikeStats(cell.path + '/stat')
        stats.windowLength = 10
        moose.connect(spike, 'spikeOut', stats, 'addSpike')

        # P2: Ex -> Inh
        syn = moose.element(cell.path + '/d3/gluR/handler')
        rnd = nprand.rand(1, number_of_ext_cells)
        indices = where(rnd <= P2)
        for j in indices[1]:
            spike = moose.element(net +'/cell' + str(j) + '/spike')
            moose.connect(spike, 'spikeOut', syn.synapse[j], 'addSpike', 'Single')
            syn.synapse[j].delay = 2e-3 + (8e-3 - 2e-3) * nprand.random_sample()  # random

    # P3: Inh -> Ex
    for i in range(number_of_ext_cells):
        syn = moose.element(net+'/cell' + str(i) + '/d4/gluR/handler')
        rnd = nprand.rand(1, number_of_inh_cells)
        indices = where(rnd <= P3)
        for j in indices[1]:
            spike = moose.element(net+'/cell_in' + str(j) + '/spike')
            moose.connect(spike, 'spikeOut', syn.synapse[j], 'addSpike')
            syn.synapse[j].delay = 2e-3 + (8e-3 - 2e-3) * nprand.random_sample()  # random

    # P1: Ex -> Ex
    for i in range(number_of_ext_cells):
        syn = moose.element(net+'/cell' + str(i) + '/d3/gluR/handler')
        rnd = nprand.rand(1, number_of_ext_cells)
        indices = where(rnd <= P1)
        for j in indices[1]:
            if i == j:
                continue
            spike = moose.element(net+'/cell' + str(j) + '/spike')
            j = j + number_of_input_cells
            moose.connect(spike, 'spikeOut', syn.synapse[j], 'addSpike')
            syn.synapse[j].delay = 2e-3 + (8e-3 - 2e-3) * nprand.random_sample()  # random



def make_input_layer(avgFiringRate=10, spike_refractT=74e-4):
    _input = moose.Neutral('/in')

    stim = moose.StimulusTable(_input.path + '/stim')
    stim.vector = [avgFiringRate]
    stim.startTime = 0
    stim.stopTime = 1
    stim.loopTime = 1
    stim.stepSize = 0
    stim.stepPosition = 0
    stim.doLoop = 1

    input_layer = []
    for i in range(number_of_input_cells):
        spike = moose.RandSpike(_input.path + '/sp' + str(i))
        spike.refractT = spike_refractT
        moose.connect(stim, 'output', spike, 'setRate')
        input_layer.append(spike)

    return input_layer


def run_simulator():
    moose.Neutral('/graphs')
    moose.Neutral('/graphs/cpu')
    moose.Neutral('/graphs/cpu/stat')
    moose.Neutral('/graphs/gpu')
    moose.Neutral('/graphs/gpu/stat')
    
    moose.setClock(0, dt)
    moose.setClock(1, dt)
    moose.setClock(2, dt)
    moose.setClock(8, 2e-4)
    
    input_layer = make_input_layer()

    create_cells("/net", input_layer)

    if Use_CPU:
        for i in range(number_of_ext_cells):
            add_plot("/net/cell" + str(i) + '/soma','getVm', 'cpu/c' + str(i) + '_soma')
            add_plot("/net/cell" + str(i) + '/stat','getMean', 'cpu/stat/c' + str(i))
        for i in range(number_of_inh_cells):
            add_plot("/net/cell_in" + str(i) + '/soma','getVm', 'cpu/c_in' + str(i) + '_soma')
            add_plot("/net/cell_in" + str(i) + '/stat','getMean', 'cpu/stat/c_in' + str(i))

        moose.useClock(0, '/##', 'init')
        moose.useClock(1, '/##', 'process')
        moose.useClock(8, '/graphs/##', 'process')
        moose.reinit()
        
        start_time = time.time()
        moose.start(Simulation_Time)
        t_exec = time.time() - start_time    
        print("--- Exec: %s ms" % str(t_exec * dt / Simulation_Time * 1000))
        
        dump_plots()
    
    moose.reinit()
    # Assign HSolve objects
    net = "net"
    for i in range(number_of_ext_cells):
        hsolve = moose.HSolve(net+ '/cell' + str(i) + '/hsolve')
        hsolve.dt = dt
        hsolve.target = net +'/cell' + str(i) + '/soma'
    for i in range(number_of_inh_cells):
        hsolve = moose.HSolve(net + '/cell_in' + str(i) + '/hsolve')
        hsolve.dt = dt
        hsolve.target = net + '/cell_in' + str(i) + '/soma'
        
    if Use_GPU:
        hsolve = moose.HSolve('/net/hsolve')
        hsolve.dt = dt
        hsolve.target = '/net'
        
        for i in range(number_of_ext_cells):
            add_plot("/net/cell" + str(i) + '/soma','getVm', 'gpu/c' + str(i) + '_soma')
            add_plot("/net/cell" + str(i) + '/stat','getMean', 'gpu/stat/c' + str(i))
        for i in range(number_of_inh_cells):
            add_plot("/net/cell_in" + str(i) + '/soma','getVm', 'gpu/c_in' + str(i) + '_soma')
            add_plot("/net/cell_in" + str(i) + '/stat','getMean', 'gpu/stat/c_in' + str(i))

        moose.useClock(0, '/##', 'init')
        moose.useClock(1, '/##', 'process')
        moose.useClock(8, '/graphs/##', 'process')
        moose.reinit()
        
        start_time = time.time()
        moose.start(Simulation_Time)
        t_exec = time.time() - start_time
        
        save_plots()
        print("--- Exec: %s ms" % str(t_exec * dt / Simulation_Time * 1000))
        
        dump_plots()
        
   


Use_CPU = True
Use_GPU = True

Simulation_Time = 2

number_of_input_cells = 10
number_of_ext_cells = 100
number_of_inh_cells = 20


IC = .2  # Input connection probability
P1 = .2 # Exitatory to Excitatory connection probability
P2 = .4  # Exitatory to Inhibitory connection probability
P3 = .4  # Inhibitory to Excitatory connection probability

INJECT_CURRENT = 0
dt = 2e-6

if __name__ == '__main__':
    run_simulator()