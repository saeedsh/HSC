#/**********************************************************************
#** This program is part of 'MOOSE', the
#** Messaging Object Oriented Simulation Environment,
#** also known as GENESIS 3 base code.
#**           copyright (C) 2004 Upinder S. Bhalla. and NCBS
#** It is made available under the terms of the
#** GNU General Public License version 2
#** See the file COPYING.LIB for the full notice.
#**********************************************************************/
#TODO: imported from main Makefile for test, after we can remove it
ifndef CXXFLAGS 
	CXXFLAGS = -g -fpermissive -fno-strict-aliasing -fPIC -fno-inline-functions \
	-Wall -Wno-long-long -pedantic -DDO_UNIT_TESTS -DUSE_GENESIS_PARSER -DSVN_REVISION=\"5340M\" \
	-DLINUX -DUSE_GSL -DUSE_HDF5  -DH5_NO_DEPRECATED_SYMBOLS -I/usr/local/hdf5/include 
endif

ifndef CUDAFLAGS 
	CUDAFLAGS = -G -O0 -Xcompiler -fopenmp -Xcompiler -fPIC -g -gencode arch=compute_30,code=compute_30 -gencode arch=compute_30,code=sm_30 -x cu  -I./libs -I./libs/tbb/include
endif
####################################################################

TARGET = _pn2s.o

COBJS += Device.o \
	DeviceManager.o 
		 
OBJS += ResourceManager.o \
	Parameters.o  

SUBDIR = core
	
MODULES = core/_core.o 

.PHONY: all
all: $(TARGET)
default: benchmark 

Manager.o: Manager.cpp Manager.h headers.h Parameters.h
Device.o: Device.cpp Device.h headers.h Parameters.h
DeviceManager.o: DeviceManager.cpp DeviceManager.h headers.h Parameters.h 
ResourceManager.o: ResourceManager.cpp ResourceManager.h DeviceManager.cpp DeviceManager.h headers.h Parameters.h
Parameters.o: Parameters.cpp Parameters.h

$(TARGET): $(OBJS) $(COBJS) $(SUBDIR) 
	$(LD) -r -o  $(TARGET) $(OBJS) $(COBJS) $(MODULES)
	 
$(OBJS):
	$(CXX) $(CXXFLAGS) $(SMOLDYN_FLAGS) -I/usr/local/cuda/include -I. -I../../basecode -I../../msg -I./libs $< -c 
	
$(COBJS):
	nvcc --compile $(CUDAFLAGS) -o  "$@" "$<"     

.PHONY: clean
$(SUBDIR): force
	@(for i in $(SUBDIR) ; do $(MAKE) -C $$i; done)

.PHONY: force
force :;

benchmark: $(TARGET) force
	$(CXX) -fopenmp $(CXXFLAGS) $(TARGET) -o benchmark -L/usr/local/cuda/lib64 -lcuda -lcudart -lcublas -I/usr/local/cuda/include -I./libs -I./libs/tbb/include Benchmark.cpp  

clean:
	@(for i in $(SUBDIR) ; do $(MAKE) -C $$i clean;  done)
	rm -rf $(OBJS) $(COBJS) $(TARGET) Test benchmark test_perf
	
