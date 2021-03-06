///////////////////////////////////////////////////////////
//  SolverGates.h
//  Implementation of the Class SolverGates
//  Created on:      27-Dec-2013 7:57:50 PM
//  Original author: Saeed Shariati
///////////////////////////////////////////////////////////

#pragma once

#include "../../headers.h"
#include "PField.h"
#include "ModelStatistic.h"

namespace pn2s
{
namespace models
{
class SolverGates
{
private:

	ModelStatistic _m_statistic;
	cudaStream_t _stream;


	PField<TYPE_>  _state;
	PField<TYPE_>  _gk;
	PField<TYPE_>  _ch_currents_gk;
	PField<TYPE_>  _ch_currents_gkek;

	//Constant values
	PField<TYPE_>  _power;
	PField<pn2s::models::GateParams> _params; //10 values
	PField<TYPE3_> _params_div_min_max;
	PField<TYPE_> _gbar;
	PField<TYPE_>  _ek;

	//indexes
	PField<int>  _comptIndex;
	PField<int>  _channelIndex;
	PField<int>  _gateIndex;

	// External fields
	PField<TYPE_>*  _Vm;
	PField<TYPE_>*  _rhs;
	PField<TYPE_>*  _hm;

	size_t _nCompt;
public:
	dim3 _threads, _blocks;
	SolverGates();
	~SolverGates();
	size_t AllocateMemory(models::ModelStatistic& s, cudaStream_t stream);
	void PrepareSolver(PField<TYPE_>*  Vm, PField<TYPE_>*  hm,  PField<TYPE_>*  rhs);
	double Input();
	double Process();
	double Output();

	PField<TYPE_> * GetFieldGK(){return & _ch_currents_gk;}
	PField<TYPE_> * GetFieldEK(){return & _ch_currents_gkek;}

	double GetDt(){ return _m_statistic.dt;}
	void SetDt(double dt){ _m_statistic.dt = dt;}

	void 	SetGateParams(int index, vector<double>& params);

	void 	SetValue(int index, FIELD::GATE, TYPE_ value);
	TYPE_ 	GetValue(int index, FIELD::GATE);
};

}
}

