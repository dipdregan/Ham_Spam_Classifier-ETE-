import os
import logging
import pandas as pd
from tensorflow.keras.models import load_model
from sklearn.metrics import confusion_matrix
from src.constant.constants import *
from src.entity.config_entity import ModelEvaluatorConfig
from src.entity.artifact_entity import DataTransformationArtifact, ModelTrainerArtifact,ModelEvaluatorArtifact
from src.exception import ham_spam
from src.utils import load_data, preprocess_data
from src.plot import plot_confusion_matrix,plot_training_history
from src.models.label_encoding import LabelConverter
import mlflow

class ModelEvaluator:
    def __init__(self, model_evaluation_config:ModelEvaluatorConfig,
                model_trainer_artifact: ModelTrainerArtifact,
                data_transformation_artifact: DataTransformationArtifact):
        
        self.config = model_evaluation_config
        self.model_trainer_artifact = model_trainer_artifact
        self.test_data_path = data_transformation_artifact.test_file_path
        # self.model_file_path = self.model_trainer_artifact.model_file_path

        self.__params = PARAMS_FILE['model_params']
        self.__data_processing_params = self.__params['data_processing']
        self.__max_words = self.__data_processing_params['max_words']
        self.__max_sequence_length = self.__data_processing_params['max_sequence_length']

    def initiate_model_evaluation(self)->ModelEvaluatorArtifact:
        try:
            logging.info('Loading test data...')
            test_texts, test_labels = load_data(self.test_data_path,
                                                feature_name=FEATURES_NAME,
                                                target=TARGET_NAME)

            logging.info('Preprocessing test data...')
            test_padded = preprocess_data(feature=test_texts,
                                        max_words=self.__max_words,
                                        max_sequence_length=self.__max_sequence_length)

            logging.info('Loading the trained model...')
            trained_model = load_model(self.model_trainer_artifact.model_file_path)

            logging.info('Evaluating the model on the test data...')
            evaluation_results = trained_model.evaluate(test_padded, test_labels)
            logging.info(f'Model evaluation results: {evaluation_results}')

            # Calculate confusion matrix
            y_true = test_labels
            y_probabilities = trained_model.predict(test_padded)
            y_pred = (y_probabilities > 0.5).astype(int).reshape(-1)
            cm = confusion_matrix(y_true, y_pred)

            # Instantiate label converter
            label_converter = LabelConverter()
            # Define save path
            report = self.config.evaluation_report
            os.makedirs(report, exist_ok=True)

            # Plot confusion matrix
            plot_confusion_matrix(cm,
                                classes=[0, 1],
                                label_converter=label_converter,
                                save_path=report)
            
            # trainer_artifact, trainer_history = self.model_trainer_artifact
            # plot_training_history(trainer_history,report)

            accuracy_threshold = 0.8

            # Log to MLflow
            with mlflow.start_run() as run:
                mlflow.log_params({"max_words": self.__max_words,
                                   "max_sequence_length": self.__max_sequence_length})

                # Log evaluation results
                mlflow.log_metrics({"accuracy": evaluation_results[1],
                                    "confusion_matrix": str(cm)})

                if evaluation_results[1] >= accuracy_threshold:
                    # Create a folder for accepted models
                    accepted_models_folder = self.config.accepted_model
                    os.makedirs(accepted_models_folder, exist_ok=True)

                    # Save the accepted model in the accepted_models folder
                    accepted_model_path = os.path.join(accepted_models_folder, 'accepted_model.h5')
                    trained_model.save(accepted_model_path)
                    mlflow.log_artifact(accepted_model_path)
                    logging.info(f'Accepted model saved to: {accepted_model_path}')
                    mlflow.log_params({"model_status": "accepted"})
                    
                else:
                    logging.warning(f'Model accuracy ({evaluation_results[1]:.4f}) is below the threshold. Rejecting the model.')

                    # Create a folder for rejected models
                    rejected_models_folder = self.config.rejected_model
                    os.makedirs(rejected_models_folder, exist_ok=True)

                    # Save the rejected model in the rejected_models folder
                    rejected_model_path = os.path.join(rejected_models_folder, 'rejected_model.h5')
                    trained_model.save(rejected_model_path)
                    mlflow.log_artifact(rejected_model_path)
                    logging.info(f'Rejected model saved to: {rejected_model_path}')
                    mlflow.log_params({"model_status": "rejected"})

            model_evaluation_artifact = ModelEvaluatorArtifact(
                accepted_model_path=accepted_model_path,
                rejected_model_path=rejected_model_path,
                evaluation_report_path=report
                )
            return model_evaluation_artifact
            

        except Exception as e:
            logging.error(f'Error during model evaluation: {str(e)}')
            mlflow.log_params({"model_status": "error"})
            return False
