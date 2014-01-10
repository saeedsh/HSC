///////////////////////////////////////////////////////////
//  HSC_SolverData.h
//  Implementation of the Classes related to HSC_Solver
//  Created on:      27-Dec-2013 7:29:01 PM
//  Original author: Saeed Shariati
///////////////////////////////////////////////////////////

#if !defined(A73EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_)
#define A73EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_
#include "HSC_SolverChannels.h"
#include "HSC_SolverComps.h"
#include "HSC_NetworkAnalyzer.h"

class HSC_SolverData
{
public:
	HSC_SolverData();
	virtual ~HSC_SolverData();

	double GetDt(){ return _dt;}
	void SetDt(double dt){ _dt = dt; _compsSolver.SetDt(dt);}

	hscError PrepareSolver(vector<HSCModel > &models);

	hscError Process();
//	vector<vector<HSCModel_Base> > models; //TODO: Encapsulation

private:
	double _dt;
	HSC_NetworkAnalyzer _analyzer;
	HSC_SolverChannels _channelSolver;
	HSC_SolverComps<double,ARCH_SM30> _compsSolver;

};
#endif // !defined(A73EC9AE3_8C2D_45e3_AE47_0F3CC8B2E661__INCLUDED_)