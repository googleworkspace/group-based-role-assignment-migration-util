#!/usr/bin/python
#
# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Singleton class for Logger."""
import datetime
import logging
import os
import textwrap
from typing import TypeVar
import tabulate


T = TypeVar("T")  # TypeVar for the class type


# TODOG make a UserSelection singleton
class Logger:
  """Singleton class for Logger."""

  instance: "Logger" = None
  log_path: str = None
  debug_mode: bool = False
  logger: logging.Logger = None

  @classmethod
  def initialize(cls, output_path: str, debug_mode: bool) -> None:
    if not cls.instance:
      cls.instance = cls.__new__(cls)
      cls.instance.initialize_logger(output_path, debug_mode)

  @classmethod
  def get_instance(cls) -> "Logger":
    if not cls.instance:
      raise AssertionError("Expected to be initialized before use")
    return cls.instance

  def initialize_logger(self, output_path: str, debug_mode: bool) -> None:
    """Initialize the logger which is a singleton."""
    self.debug_mode = debug_mode
    self.logger = logging.getLogger("")
    self.logger.setLevel(logging.INFO)

    # Remove existing handlers (if any) to avoid duplicate log messages
    for handler in self.logger.handlers[:]:
      self.logger.removeHandler(handler)

    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime("%Y-%m-%d_%H-%M-%S")
    log_name = f"log_{formatted_time}.log"

    self.log_path = os.path.join(output_path, log_name)

    # Create a file handler
    self.file_handler = logging.FileHandler(self.log_path)
    self.file_handler.setFormatter(logging.Formatter("%(message)s"))
    
    self.console = logging.StreamHandler()                                               
    self.console.setLevel(logging.INFO)                                                  
    self.console.setFormatter(logging.Formatter("%(message)s"))                                               

    # Add handlers to the logger
    self.logger.addHandler(self.file_handler)
    self.logger.addHandler(self.console) 
    self.log("Writing logs to: {}".format(self.log_path))

  def header(self, message: str) -> None:
    self.log(
        "\n**********************************************************************"
    )
    self.log(message)
    self.log(
        "**********************************************************************"
    )

  def debug(self, text: str) -> None:
    if self.debug_mode:
      self.log_indented("[DEBUG]: {}".format(text))

  def log_table(self, headers: list[str], contents: list[list[str]]) -> None:
    self.log(tabulate.tabulate(contents, headers=headers, tablefmt="grid"))

  def log_indented(self, text: str) -> None:
    self.log(
        textwrap.fill(
            text, width=180, initial_indent="\t", subsequent_indent="\t  "
        )
    )

  def log(self, message: str) -> None:
    if self.logger:
      self.logger.info(message)

  def get_log_path(self) -> str:
    if not self.log_path:
      raise AssertionError("Expected to be initialized before use")
    return self.log_path
