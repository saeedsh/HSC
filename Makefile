#/**********************************************************************
#** This program is part of 'MOOSE', the
#** Messaging Object Oriented Simulation Environment,
#** also known as GENESIS 3 base code.
#**           copyright (C) 2004 Upinder S. Bhalla. and NCBS
#** It is made available under the terms of the
#** GNU General Public License version 2
#** See the file COPYING.LIB for the full notice.
#**********************************************************************/

TARGET = _hsolveCuda.o
CLIB = HSC/_hsc.o
OBJ = \
	HSolveStruct.o \
	HinesMatrix.o \
	HSolvePassive.o \
	RateLookup.o \
	HSolveActive.o \
	HSolveActiveSetup.o \
	HSolveInterface.o \
	HSolve.o \
	HSolveUtils.o \
	testHSolve.o \
	ZombieCompartment.o \
	ZombieCaConc.o \
	ZombieHHChannel.o \
	HSC_Proxy.o

HEADERS = \
	../basecode/header.h

SUBDIR = \
	HSC

default: $(TARGET)

$(OBJ)	: $(HEADERS)
HSolveStruct.o:	HSolveStruct.h
HinesMatrix.o:	HinesMatrix.h TestHSolve.h HinesMatrix.cpp
HSolvePassive.o:	HSolvePassive.h HinesMatrix.h HSolveStruct.h HSolveUtils.h TestHSolve.h ../biophysics/Compartment.h
RateLookup.o:	RateLookup.h
HSolveActive.o:	HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h
HSolveActiveSetup.o:	HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h HSolveUtils.h ../biophysics/HHChannel.h ../biophysics/ChanBase.h ../biophysics/HHGate.h ../biophysics/CaConc.h
HSolveInterface.o:	HSolve.h HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h
HSolve.o:	../biophysics/Compartment.h ZombieCompartment.h ../biophysics/CaConc.h ZombieCaConc.h ../biophysics/HHGate.h ../biophysics/ChanBase.h ../biophysics/HHChannel.h ZombieHHChannel.h HSolve.h HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h ../basecode/ElementValueFinfo.h
ZombieCompartment.o:	ZombieCompartment.h ../randnum/randnum.h ../biophysics/Compartment.h HSolve.h HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h ../basecode/ElementValueFinfo.h
ZombieCaConc.o:	ZombieCaConc.h ../biophysics/CaConc.h HSolve.h HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h ../basecode/ElementValueFinfo.h
ZombieHHChannel.o:	ZombieHHChannel.h ../biophysics/HHChannel.h ../biophysics/ChanBase.h ../biophysics/HHGate.h HSolve.h HSolveActive.h RateLookup.h HSolvePassive.h HinesMatrix.h HSolveStruct.h ../basecode/ElementValueFinfo.h
HSC_Proxy.o:	HSC_Proxy.cpp	HSC_Proxy.h

.cpp.o:
	$(CXX) $(CXXFLAGS) $(SMOLDYN_FLAGS) -I. -I../basecode -I../msg $< -c -I/usr/local/cuda/include

$(TARGET): $(OBJ) $(SMOLDYN_OBJ) $(HEADERS)
	@(for i in $(SUBDIR) ; do $(MAKE) -C $$i; done)
	$(LD) -r -o $(TARGET) $(OBJ) $(SMOLDYN_OBJ) $(SMOLDYN_LIB_PATH) $(SMOLDYN_LIBS) $(GSL_LIBS) $(CLIB) 

clean:
	@(for i in $(SUBDIR) ; do $(MAKE) -C $$i clean;  done)
	rm -f *.o $(TARGET) core core.*
