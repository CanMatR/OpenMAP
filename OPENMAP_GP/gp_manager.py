import numpy as np

from GPy import kern
from GPy.models import GPRegression

from GPyOpt import Design_space
from GPyOpt.acquisitions import AcquisitionLCB
from GPyOpt.core import evaluators
from GPyOpt.core.task import objective
from GPyOpt.methods import ModularBayesianOptimization
from GPyOpt.models import GPModel
from GPyOpt.optimization.acquisition_optimizer import AcquisitionOptimizer


class gp_manager:

    def save_model(self, output_filename):
        self.model.save_model(output_filename)

    def load_model(self, output_filename):
        zip_filename = output_filename + ".zip"
        self.model = GPRegression.load_model(zip_filename)

    def train_model(self, inpar, loss, max_iters=100):
        self.kernel = kern.RBF(input_dim = inpar.shape[1])
        self.model = GPRegression(inpar, loss, self.kernel)
        self.model.optimize('bfgs', max_iters=max_iters)

    def retrain_model(self, inpar, loss, max_iters=100):
        raise( Exception("use train_model instead") )
#        self.model.set_XY(inpar, loss)
#        self.model.optimize('bfgs', max_iters=max_iters)

    def pre_suggest(self, domain):
        self.space = Design_space( domain )
        self.objective = objective.Objective()
        self.acq_opt = AcquisitionOptimizer(self.space)

    def suggest_single(self, exploration_weight=2):
        opt_model = GPModel(optimize_restarts=1, verbose=False)
        opt_model.model = self.model

        acquisition = AcquisitionLCB(opt_model, self.space, self.acq_opt, exploration_weight=exploration_weight)
        evaluator = evaluators.Sequential(acquisition)

        bo = ModularBayesianOptimization(opt_model, self.space, self.objective, acquisition, evaluator,
                                            X_init = self.model.X,
                                            Y_init = self.model.Y,
                                            normalize_Y = False,
                                            de_duplication = True
                                        )

        return bo.suggest_next_locations()

    def suggest_multi(self, batch_size, exploration_weight=2):
        opt_model = GPModel(optimize_restarts=1, verbose=False)
        opt_model.model = self.model

        acquisition = AcquisitionLCB(opt_model, self.space, self.acq_opt, exploration_weight=exploration_weight)
        evaluator = evaluators.ThompsonBatch(acquisition, batch_size=batch_size)

        bo = ModularBayesianOptimization(opt_model, self.space, self.objective, acquisition, evaluator,
                                            X_init = self.model.X,
                                            Y_init = self.model.Y,
                                            normalize_Y = False,
                                            de_duplication = True
                                        )

        return bo.suggest_next_locations()
