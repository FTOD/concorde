# Project review contracts

The exact shapes of what [Project review](module.md) returns and keeps. The report is the `output`
of the [run result](../../glossary.json#concept.run-result). The review record is the file the
Operation commits on the primary branch.

Each [Module](../../glossary.json#concept.module)'s [Spec](../../glossary.json#concept.spec)
panel and code review inside the report keep the shape their own Operations give them:

- A Spec panel is one Module's item of the
  [panel payload](../spec-review/panel.md#contract.spec-review.panel-payload).
- A code review is one Module's item of the
  [code review report](../code-review/contracts.md#contract.code-review.review).

Where the issues part is not installed, the report has the same shape:

- Every finding's `issue` is null.
- Every `earlier_issues` is null, since none were read.
- Every Module's `standing` is empty, and its outcome follows from this run's findings.
- The report's summary says that its findings were not recorded as Issues.

## Project review report

```concorde-contract
{
  "id": "contract.project-review.report",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "verdict",
      "full",
      "validation",
      "checks",
      "deterministic",
      "architecture",
      "modules",
      "standing",
      "record",
      "workflow"
    ],
    "properties": {
      "verdict": {
        "enum": [
          "accepted",
          "changes_required",
          "incomplete"
        ]
      },
      "full": {
        "type": "boolean"
      },
      "workflow": {
        "type": "object"
      },
      "validation": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "errors",
          "warnings"
        ],
        "properties": {
          "errors": {
            "type": "integer",
            "minimum": 0
          },
          "warnings": {
            "type": "integer",
            "minimum": 0
          }
        }
      },
      "checks": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "check",
            "module",
            "outcome",
            "exit_code",
            "log"
          ],
          "properties": {
            "check": {
              "type": "string",
              "minLength": 1
            },
            "module": {
              "type": "string",
              "pattern": "^module\\."
            },
            "outcome": {
              "enum": [
                "passed",
                "failed",
                "timed_out"
              ]
            },
            "exit_code": {
              "anyOf": [
                {
                  "type": "integer"
                },
                {
                  "type": "null"
                }
              ]
            },
            "log": {
              "type": "string",
              "minLength": 1
            }
          }
        }
      },
      "deterministic": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "complete",
          "findings",
          "unowned",
          "earlier_issues"
        ],
        "properties": {
          "complete": {
            "type": "boolean"
          },
          "findings": {
            "type": "array",
            "items": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "phase",
                "module",
                "title",
                "tier",
                "severity",
                "subjects",
                "issue"
              ],
              "properties": {
                "phase": {
                  "enum": [
                    "check",
                    "coverage",
                    "unowned"
                  ]
                },
                "module": {
                  "type": "string",
                  "minLength": 1
                },
                "title": {
                  "type": "string",
                  "minLength": 1
                },
                "tier": {
                  "enum": [
                    "suggestion",
                    "obvious-fix",
                    "preferred-fix",
                    "decision-needed"
                  ]
                },
                "severity": {
                  "enum": [
                    "critical",
                    "high",
                    "medium",
                    "low"
                  ]
                },
                "subjects": {
                  "type": "array",
                  "minItems": 1,
                  "items": {
                    "type": "string",
                    "minLength": 1
                  }
                },
                "issue": {
                  "anyOf": [
                    {
                      "type": "string",
                      "pattern": "^I-[0-9a-f]{32}$"
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "earlier": {
                  "type": "string",
                  "pattern": "^I-[0-9a-f]{32}$"
                }
              }
            }
          },
          "unowned": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "earlier_issues": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "carried",
                  "resolved"
                ],
                "properties": {
                  "carried": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "issue",
                        "severity",
                        "tier",
                        "title"
                      ],
                      "properties": {
                        "issue": {
                          "type": "string",
                          "pattern": "^I-[0-9a-f]{32}$"
                        },
                        "severity": {
                          "anyOf": [
                            {
                              "enum": [
                                "critical",
                                "high",
                                "medium",
                                "low"
                              ]
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "tier": {
                          "anyOf": [
                            {
                              "enum": [
                                "suggestion",
                                "obvious-fix",
                                "preferred-fix",
                                "decision-needed"
                              ]
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "title": {
                          "type": "string",
                          "minLength": 1
                        }
                      }
                    }
                  },
                  "resolved": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "issue",
                        "reason"
                      ],
                      "properties": {
                        "issue": {
                          "type": "string",
                          "pattern": "^I-[0-9a-f]{32}$"
                        },
                        "reason": {
                          "type": "string",
                          "minLength": 1
                        }
                      }
                    }
                  }
                }
              }
            ]
          }
        }
      },
      "architecture": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "state",
          "complete",
          "context_identity",
          "review"
        ],
        "properties": {
          "state": {
            "enum": [
              "reviewed",
              "skipped",
              "left_out"
            ]
          },
          "complete": {
            "type": "boolean"
          },
          "context_identity": {
            "anyOf": [
              {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$"
              },
              {
                "type": "null"
              }
            ]
          },
          "review": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "object",
                "required": [
                  "module",
                  "outcome",
                  "context_identity",
                  "architecture_identity",
                  "reviews",
                  "findings",
                  "rejected",
                  "earlier_issues"
                ],
                "additionalProperties": false,
                "properties": {
                  "module": {
                    "type": "string",
                    "minLength": 1
                  },
                  "outcome": {
                    "enum": [
                      "accepted",
                      "changes_required",
                      "incomplete"
                    ]
                  },
                  "context_identity": {
                    "anyOf": [
                      {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$"
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "architecture_identity": {
                    "anyOf": [
                      {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$"
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "reviews": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "worker",
                        "role",
                        "seat",
                        "status",
                        "findings",
                        "rejected",
                        "resolved"
                      ],
                      "properties": {
                        "worker": {
                          "enum": [
                            "reviewer1",
                            "reviewer2",
                            "reviewer3",
                            "reviewer4",
                            "reviewer5",
                            "architect1",
                            "architect2"
                          ]
                        },
                        "role": {
                          "enum": [
                            "reviewer",
                            "architect"
                          ]
                        },
                        "seat": {
                          "type": "integer",
                          "minimum": 1
                        },
                        "status": {
                          "enum": [
                            "ok",
                            "blocked",
                            "failed"
                          ]
                        },
                        "findings": {
                          "type": "array",
                          "items": {
                            "$ref": "#/$defs/labelled"
                          }
                        },
                        "rejected": {
                          "type": "array",
                          "items": {
                            "$ref": "#/$defs/unusable"
                          }
                        },
                        "resolved": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "issue",
                              "reason"
                            ],
                            "properties": {
                              "issue": {
                                "type": "string",
                                "minLength": 1
                              },
                              "reason": {
                                "type": "string",
                                "minLength": 1
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "findings": {
                    "type": "array",
                    "items": {
                      "$ref": "#/$defs/reported"
                    }
                  },
                  "rejected": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "source",
                        "reason"
                      ],
                      "properties": {
                        "source": {
                          "type": "string",
                          "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
                        },
                        "reason": {
                          "type": "string",
                          "minLength": 1
                        }
                      }
                    }
                  },
                  "earlier_issues": {
                    "anyOf": [
                      {
                        "type": "null"
                      },
                      {
                        "type": "object",
                        "additionalProperties": false,
                        "required": [
                          "carried",
                          "resolved",
                          "ignored"
                        ],
                        "properties": {
                          "carried": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": false,
                              "required": [
                                "issue",
                                "severity",
                                "tier",
                                "title"
                              ],
                              "properties": {
                                "issue": {
                                  "type": "string",
                                  "pattern": "^I-[0-9a-f]{32}$"
                                },
                                "severity": {
                                  "anyOf": [
                                    {
                                      "enum": [
                                        "critical",
                                        "high",
                                        "medium",
                                        "low"
                                      ]
                                    },
                                    {
                                      "type": "null"
                                    }
                                  ]
                                },
                                "tier": {
                                  "anyOf": [
                                    {
                                      "enum": [
                                        "suggestion",
                                        "obvious-fix",
                                        "preferred-fix",
                                        "decision-needed"
                                      ]
                                    },
                                    {
                                      "type": "null"
                                    }
                                  ]
                                },
                                "title": {
                                  "type": "string",
                                  "minLength": 1
                                }
                              }
                            }
                          },
                          "resolved": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": false,
                              "required": [
                                "issue",
                                "reason"
                              ],
                              "properties": {
                                "issue": {
                                  "type": "string",
                                  "pattern": "^I-[0-9a-f]{32}$"
                                },
                                "reason": {
                                  "type": "string",
                                  "minLength": 1
                                }
                              }
                            }
                          },
                          "ignored": {
                            "type": "array",
                            "items": {
                              "type": "object",
                              "additionalProperties": false,
                              "required": [
                                "issue",
                                "reason"
                              ],
                              "properties": {
                                "issue": {
                                  "type": "string",
                                  "minLength": 1
                                },
                                "reason": {
                                  "type": "string",
                                  "minLength": 1
                                }
                              }
                            }
                          }
                        }
                      }
                    ]
                  }
                }
              }
            ]
          }
        }
      },
      "modules": {
        "type": "array",
        "items": {
          "type": "object",
          "additionalProperties": false,
          "required": [
            "module",
            "outcome",
            "identities",
            "panel",
            "code_review",
            "standing"
          ],
          "properties": {
            "module": {
              "type": "string",
              "minLength": 1
            },
            "outcome": {
              "enum": [
                "accepted",
                "changes_required",
                "incomplete"
              ]
            },
            "identities": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "spec",
                "code",
                "code_digest"
              ],
              "properties": {
                "spec": {
                  "anyOf": [
                    {
                      "type": "string",
                      "pattern": "^sha256:[0-9a-f]{64}$"
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "code": {
                  "anyOf": [
                    {
                      "type": "string",
                      "pattern": "^sha256:[0-9a-f]{64}$"
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "code_digest": {
                  "anyOf": [
                    {
                      "type": "string",
                      "pattern": "^sha256:[0-9a-f]{64}$"
                    },
                    {
                      "type": "null"
                    }
                  ]
                }
              }
            },
            "panel": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "state",
                "review"
              ],
              "properties": {
                "state": {
                  "enum": [
                    "reviewed",
                    "skipped",
                    "not_run"
                  ]
                },
                "review": {
                  "anyOf": [
                    {
                      "type": "null"
                    },
                    {
                      "type": "object",
                      "required": [
                        "module",
                        "outcome",
                        "context_identity",
                        "architecture_identity",
                        "reviews",
                        "findings",
                        "rejected",
                        "earlier_issues"
                      ],
                      "additionalProperties": false,
                      "properties": {
                        "module": {
                          "type": "string",
                          "minLength": 1
                        },
                        "outcome": {
                          "enum": [
                            "accepted",
                            "changes_required",
                            "incomplete"
                          ]
                        },
                        "context_identity": {
                          "anyOf": [
                            {
                              "type": "string",
                              "pattern": "^sha256:[0-9a-f]{64}$"
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "architecture_identity": {
                          "anyOf": [
                            {
                              "type": "string",
                              "pattern": "^sha256:[0-9a-f]{64}$"
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "reviews": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "worker",
                              "role",
                              "seat",
                              "status",
                              "findings",
                              "rejected",
                              "resolved"
                            ],
                            "properties": {
                              "worker": {
                                "enum": [
                                  "reviewer1",
                                  "reviewer2",
                                  "reviewer3",
                                  "reviewer4",
                                  "reviewer5",
                                  "architect1",
                                  "architect2"
                                ]
                              },
                              "role": {
                                "enum": [
                                  "reviewer",
                                  "architect"
                                ]
                              },
                              "seat": {
                                "type": "integer",
                                "minimum": 1
                              },
                              "status": {
                                "enum": [
                                  "ok",
                                  "blocked",
                                  "failed"
                                ]
                              },
                              "findings": {
                                "type": "array",
                                "items": {
                                  "$ref": "#/$defs/labelled"
                                }
                              },
                              "rejected": {
                                "type": "array",
                                "items": {
                                  "$ref": "#/$defs/unusable"
                                }
                              },
                              "resolved": {
                                "type": "array",
                                "items": {
                                  "type": "object",
                                  "additionalProperties": false,
                                  "required": [
                                    "issue",
                                    "reason"
                                  ],
                                  "properties": {
                                    "issue": {
                                      "type": "string",
                                      "minLength": 1
                                    },
                                    "reason": {
                                      "type": "string",
                                      "minLength": 1
                                    }
                                  }
                                }
                              }
                            }
                          }
                        },
                        "findings": {
                          "type": "array",
                          "items": {
                            "$ref": "#/$defs/reported"
                          }
                        },
                        "rejected": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "source",
                              "reason"
                            ],
                            "properties": {
                              "source": {
                                "type": "string",
                                "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
                              },
                              "reason": {
                                "type": "string",
                                "minLength": 1
                              }
                            }
                          }
                        },
                        "earlier_issues": {
                          "anyOf": [
                            {
                              "type": "null"
                            },
                            {
                              "type": "object",
                              "additionalProperties": false,
                              "required": [
                                "carried",
                                "resolved",
                                "ignored"
                              ],
                              "properties": {
                                "carried": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "severity",
                                      "tier",
                                      "title"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "pattern": "^I-[0-9a-f]{32}$"
                                      },
                                      "severity": {
                                        "anyOf": [
                                          {
                                            "enum": [
                                              "critical",
                                              "high",
                                              "medium",
                                              "low"
                                            ]
                                          },
                                          {
                                            "type": "null"
                                          }
                                        ]
                                      },
                                      "tier": {
                                        "anyOf": [
                                          {
                                            "enum": [
                                              "suggestion",
                                              "obvious-fix",
                                              "preferred-fix",
                                              "decision-needed"
                                            ]
                                          },
                                          {
                                            "type": "null"
                                          }
                                        ]
                                      },
                                      "title": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                },
                                "resolved": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "reason"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "pattern": "^I-[0-9a-f]{32}$"
                                      },
                                      "reason": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                },
                                "ignored": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "reason"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "minLength": 1
                                      },
                                      "reason": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          ]
                        }
                      }
                    }
                  ]
                }
              }
            },
            "code_review": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "state",
                "review"
              ],
              "properties": {
                "state": {
                  "enum": [
                    "reviewed",
                    "skipped",
                    "not_run"
                  ]
                },
                "review": {
                  "anyOf": [
                    {
                      "type": "null"
                    },
                    {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "module",
                        "outcome",
                        "context_identity",
                        "summary",
                        "findings",
                        "rejected",
                        "earlier_issues"
                      ],
                      "properties": {
                        "module": {
                          "type": "string",
                          "pattern": "^module\\."
                        },
                        "outcome": {
                          "enum": [
                            "accepted",
                            "changes_required",
                            "incomplete"
                          ]
                        },
                        "context_identity": {
                          "anyOf": [
                            {
                              "type": "string",
                              "pattern": "^sha256:[0-9a-f]{64}$"
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "summary": {
                          "anyOf": [
                            {
                              "type": "string",
                              "minLength": 1
                            },
                            {
                              "type": "null"
                            }
                          ]
                        },
                        "findings": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "module",
                              "kind",
                              "severity",
                              "tier",
                              "title",
                              "problem",
                              "impact",
                              "basis",
                              "locations",
                              "evidence",
                              "suggestion",
                              "issue"
                            ],
                            "properties": {
                              "module": {
                                "type": "string",
                                "pattern": "^module\\."
                              },
                              "kind": {
                                "enum": [
                                  "violation",
                                  "defect",
                                  "missing-test",
                                  "out-of-scope",
                                  "spec-gap",
                                  "spec-challenge"
                                ]
                              },
                              "severity": {
                                "enum": [
                                  "critical",
                                  "high",
                                  "medium",
                                  "low"
                                ]
                              },
                              "tier": {
                                "enum": [
                                  "suggestion",
                                  "obvious-fix",
                                  "preferred-fix",
                                  "decision-needed"
                                ]
                              },
                              "title": {
                                "type": "string",
                                "minLength": 1
                              },
                              "problem": {
                                "type": "string",
                                "minLength": 1
                              },
                              "impact": {
                                "type": "string",
                                "minLength": 1
                              },
                              "basis": {
                                "type": "string",
                                "minLength": 1
                              },
                              "locations": {
                                "type": "array",
                                "minItems": 1,
                                "items": {
                                  "type": "string",
                                  "minLength": 1
                                }
                              },
                              "evidence": {
                                "type": "string",
                                "minLength": 1
                              },
                              "suggestion": {
                                "type": "string",
                                "minLength": 1
                              },
                              "earlier": {
                                "type": "string",
                                "pattern": "^I-[0-9a-f]{32}$"
                              },
                              "issue": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "pattern": "^I-[0-9a-f]{32}$"
                                  },
                                  {
                                    "type": "null"
                                  }
                                ]
                              }
                            }
                          }
                        },
                        "rejected": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "finding",
                              "reason"
                            ],
                            "properties": {
                              "finding": {
                                "type": "object",
                                "additionalProperties": false,
                                "required": [
                                  "module",
                                  "kind",
                                  "severity",
                                  "tier",
                                  "title",
                                  "problem",
                                  "impact",
                                  "basis",
                                  "locations",
                                  "evidence",
                                  "suggestion"
                                ],
                                "properties": {
                                  "module": {
                                    "type": "string",
                                    "pattern": "^module\\."
                                  },
                                  "kind": {
                                    "enum": [
                                      "violation",
                                      "defect",
                                      "missing-test",
                                      "out-of-scope",
                                      "spec-gap",
                                      "spec-challenge"
                                    ]
                                  },
                                  "severity": {
                                    "enum": [
                                      "critical",
                                      "high",
                                      "medium",
                                      "low"
                                    ]
                                  },
                                  "tier": {
                                    "enum": [
                                      "suggestion",
                                      "obvious-fix",
                                      "preferred-fix",
                                      "decision-needed"
                                    ]
                                  },
                                  "title": {
                                    "type": "string",
                                    "minLength": 1
                                  },
                                  "problem": {
                                    "type": "string",
                                    "minLength": 1
                                  },
                                  "impact": {
                                    "type": "string",
                                    "minLength": 1
                                  },
                                  "basis": {
                                    "type": "string",
                                    "minLength": 1
                                  },
                                  "locations": {
                                    "type": "array",
                                    "minItems": 1,
                                    "items": {
                                      "type": "string",
                                      "minLength": 1
                                    }
                                  },
                                  "evidence": {
                                    "type": "string",
                                    "minLength": 1
                                  },
                                  "suggestion": {
                                    "type": "string",
                                    "minLength": 1
                                  }
                                }
                              },
                              "reason": {
                                "type": "string",
                                "minLength": 1
                              }
                            }
                          }
                        },
                        "earlier_issues": {
                          "anyOf": [
                            {
                              "type": "null"
                            },
                            {
                              "type": "object",
                              "additionalProperties": false,
                              "required": [
                                "carried",
                                "resolved",
                                "ignored"
                              ],
                              "properties": {
                                "carried": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "severity",
                                      "tier",
                                      "title"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "pattern": "^I-[0-9a-f]{32}$"
                                      },
                                      "severity": {
                                        "anyOf": [
                                          {
                                            "enum": [
                                              "critical",
                                              "high",
                                              "medium",
                                              "low"
                                            ]
                                          },
                                          {
                                            "type": "null"
                                          }
                                        ]
                                      },
                                      "tier": {
                                        "anyOf": [
                                          {
                                            "enum": [
                                              "suggestion",
                                              "obvious-fix",
                                              "preferred-fix",
                                              "decision-needed"
                                            ]
                                          },
                                          {
                                            "type": "null"
                                          }
                                        ]
                                      },
                                      "title": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                },
                                "resolved": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "reason"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "pattern": "^I-[0-9a-f]{32}$"
                                      },
                                      "reason": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                },
                                "ignored": {
                                  "type": "array",
                                  "items": {
                                    "type": "object",
                                    "additionalProperties": false,
                                    "required": [
                                      "issue",
                                      "reason"
                                    ],
                                    "properties": {
                                      "issue": {
                                        "type": "string",
                                        "minLength": 1
                                      },
                                      "reason": {
                                        "type": "string",
                                        "minLength": 1
                                      }
                                    }
                                  }
                                }
                              }
                            }
                          ]
                        }
                      }
                    }
                  ]
                }
              }
            },
            "standing": {
              "type": "array",
              "items": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "issue",
                  "severity",
                  "tier",
                  "title"
                ],
                "properties": {
                  "issue": {
                    "type": "string",
                    "pattern": "^I-[0-9a-f]{32}$"
                  },
                  "severity": {
                    "anyOf": [
                      {
                        "enum": [
                          "critical",
                          "high",
                          "medium",
                          "low"
                        ]
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "tier": {
                    "anyOf": [
                      {
                        "enum": [
                          "suggestion",
                          "obvious-fix",
                          "preferred-fix",
                          "decision-needed"
                        ]
                      },
                      {
                        "type": "null"
                      }
                    ]
                  },
                  "title": {
                    "type": "string",
                    "minLength": 1
                  }
                }
              }
            }
          }
        }
      },
      "standing": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "issues",
          "blocking",
          "by_severity",
          "by_tier"
        ],
        "properties": {
          "issues": {
            "type": "integer",
            "minimum": 0
          },
          "blocking": {
            "type": "integer",
            "minimum": 0
          },
          "by_severity": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "critical",
              "high",
              "medium",
              "low",
              "unrated"
            ],
            "properties": {
              "critical": {
                "type": "integer",
                "minimum": 0
              },
              "high": {
                "type": "integer",
                "minimum": 0
              },
              "medium": {
                "type": "integer",
                "minimum": 0
              },
              "low": {
                "type": "integer",
                "minimum": 0
              },
              "unrated": {
                "type": "integer",
                "minimum": 0
              }
            }
          },
          "by_tier": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "suggestion",
              "obvious-fix",
              "preferred-fix",
              "decision-needed",
              "unrated"
            ],
            "properties": {
              "suggestion": {
                "type": "integer",
                "minimum": 0
              },
              "obvious-fix": {
                "type": "integer",
                "minimum": 0
              },
              "preferred-fix": {
                "type": "integer",
                "minimum": 0
              },
              "decision-needed": {
                "type": "integer",
                "minimum": 0
              },
              "unrated": {
                "type": "integer",
                "minimum": 0
              }
            }
          }
        }
      },
      "record": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "path",
          "published",
          "commit",
          "modules",
          "architecture"
        ],
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1
          },
          "published": {
            "type": "boolean"
          },
          "commit": {
            "anyOf": [
              {
                "type": "string",
                "minLength": 1
              },
              {
                "type": "null"
              }
            ]
          },
          "modules": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "architecture": {
            "type": "boolean"
          }
        }
      }
    },
    "$defs": {
      "labelled": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "module",
          "path",
          "dimension",
          "severity",
          "tier",
          "title",
          "problem",
          "impact",
          "evidence",
          "suggestion",
          "label"
        ],
        "properties": {
          "module": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "format": "project-path"
          },
          "anchor": {
            "type": "string",
            "minLength": 1
          },
          "line": {
            "type": "integer",
            "minimum": 1
          },
          "dimension": {
            "enum": [
              "readability",
              "obligations",
              "design",
              "views",
              "terminology",
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
            ]
          },
          "severity": {
            "enum": [
              "critical",
              "high",
              "medium",
              "low"
            ]
          },
          "tier": {
            "enum": [
              "suggestion",
              "obvious-fix",
              "preferred-fix",
              "decision-needed"
            ]
          },
          "title": {
            "type": "string",
            "minLength": 1
          },
          "problem": {
            "type": "string",
            "minLength": 1
          },
          "impact": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "string",
            "minLength": 1
          },
          "suggestion": {
            "type": "string",
            "minLength": 1
          },
          "earlier": {
            "type": "string",
            "minLength": 1
          },
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "label": {
            "type": "string",
            "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
          }
        }
      },
      "reported": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "module",
          "path",
          "dimension",
          "severity",
          "tier",
          "title",
          "problem",
          "impact",
          "evidence",
          "suggestion",
          "sources",
          "note",
          "workers",
          "issue"
        ],
        "properties": {
          "module": {
            "type": "string",
            "minLength": 1
          },
          "path": {
            "type": "string",
            "format": "project-path"
          },
          "anchor": {
            "type": "string",
            "minLength": 1
          },
          "line": {
            "type": "integer",
            "minimum": 1
          },
          "dimension": {
            "enum": [
              "readability",
              "obligations",
              "design",
              "views",
              "terminology",
              "context",
              "responsibilities",
              "ownership",
              "interfaces",
              "dependencies",
              "failure-containment",
              "consistency"
            ]
          },
          "severity": {
            "enum": [
              "critical",
              "high",
              "medium",
              "low"
            ]
          },
          "tier": {
            "enum": [
              "suggestion",
              "obvious-fix",
              "preferred-fix",
              "decision-needed"
            ]
          },
          "title": {
            "type": "string",
            "minLength": 1
          },
          "problem": {
            "type": "string",
            "minLength": 1
          },
          "impact": {
            "type": "string",
            "minLength": 1
          },
          "evidence": {
            "type": "string",
            "minLength": 1
          },
          "suggestion": {
            "type": "string",
            "minLength": 1
          },
          "earlier": {
            "type": "string",
            "pattern": "^I-[0-9a-f]{32}$"
          },
          "related": {
            "type": "array",
            "items": {
              "type": "string",
              "minLength": 1
            }
          },
          "sources": {
            "type": "array",
            "minItems": 1,
            "items": {
              "type": "string",
              "pattern": "^[ra][1-9][0-9]*\\.[1-9][0-9]*$"
            }
          },
          "note": {
            "type": "string",
            "minLength": 1
          },
          "workers": {
            "type": "integer",
            "minimum": 1
          },
          "issue": {
            "anyOf": [
              {
                "type": "null"
              },
              {
                "type": "string",
                "pattern": "^I-[0-9a-f]{32}$"
              }
            ]
          }
        }
      },
      "unusable": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "finding",
          "reason"
        ],
        "properties": {
          "finding": {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "module",
              "path",
              "dimension",
              "severity",
              "tier",
              "title",
              "problem",
              "impact",
              "evidence",
              "suggestion"
            ],
            "properties": {
              "module": {
                "type": "string",
                "minLength": 1
              },
              "path": {
                "type": "string",
                "minLength": 1
              },
              "anchor": {
                "type": "string",
                "minLength": 1
              },
              "line": {
                "type": "integer",
                "minimum": 1
              },
              "dimension": {
                "enum": [
                  "readability",
                  "obligations",
                  "design",
                  "views",
                  "terminology",
                  "context",
                  "responsibilities",
                  "ownership",
                  "interfaces",
                  "dependencies",
                  "failure-containment",
                  "consistency"
                ]
              },
              "severity": {
                "enum": [
                  "critical",
                  "high",
                  "medium",
                  "low"
                ]
              },
              "tier": {
                "enum": [
                  "suggestion",
                  "obvious-fix",
                  "preferred-fix",
                  "decision-needed"
                ]
              },
              "title": {
                "type": "string",
                "minLength": 1
              },
              "problem": {
                "type": "string",
                "minLength": 1
              },
              "impact": {
                "type": "string",
                "minLength": 1
              },
              "evidence": {
                "type": "string",
                "minLength": 1
              },
              "suggestion": {
                "type": "string",
                "minLength": 1
              },
              "related": {
                "type": "array",
                "items": {
                  "type": "string",
                  "minLength": 1
                }
              }
            }
          },
          "reason": {
            "type": "string",
            "minLength": 1
          }
        }
      }
    }
  },
  "semantics": "The outcome of one project review. verdict is the highest outcome among modules in the order accepted, changes_required, incomplete, and incomplete also when deterministic.complete or architecture.complete is false or the Issues that stand could not be read. full repeats --full. validation counts the errors and warnings of the examined worktree's structural validation. checks has one item per configured check result of the work stage of the covered Modules, in the shape of the code review report's checks. deterministic.findings lists every deterministic problem the run established: phase check for a configured check that failed or timed out, coverage for a Module's scenarios no verification declaration names, unowned for the tracked files bound to no Module, which belong to the root Module; title, tier and severity are fixed per kind by the Operation, subjects names the check, the scenarios or the files, issue is the Issue that states the problem, null where the issues part is not installed or the store refused, and earlier, present only when the problem had an open Issue of its Module, kind and title, names it. unowned lists those files. earlier_issues is null where the issues part is not installed; otherwise carried lists the open deterministic Issues that still stand unchanged and resolved those whose problem the run no longer finds, for a task to close. complete is false when the checks could not run or the store refused. architecture.state is reviewed, skipped when the review-architecture context identity of every Module equals the recorded one, or left_out with --architects 0; context_identity is that identity, null when left out; review is the Spec panel payload of one Module, contract.spec-review.panel-payload, for the subject project when reviewed, else null; complete is false when the review stopped or its Issues could not all be written. modules has one item per covered Module in the registry's order. identities are what its parts would judge: spec the context identity of its review-spec grant, code that of its review-code grant and code_digest the digest of the paths and bytes of the files it binds, each null when no grant could be computed. panel and code_review each have state reviewed, skipped when the record holds the same identities, or not_run when the Module failed structural validation or has no grant, and review, the Module's item of contract.spec-review.panel-payload or of contract.code-review.review when reviewed, else null. standing lists the open Issues that spec_panel, code_review or project_review made for the Module and that no part of the run found resolved and no skipped part's record entry lists resolved at their current revision, with their severity, tier and title; where the issues part is not installed it is empty. outcome is incomplete when the Module failed structural validation, a part of it stopped, its Issues could not all be written, its checks could not run or one of its deterministic problems could not be written, changes_required when an Issue of a blocking tier stands for it, or where the issues part is not installed when a finding of a blocking tier of this run concerns it, and accepted otherwise. standing counts the Issues that stand for the covered Modules alone by severity and by tier, unrated for a report without one. record names the review record's path, whether this run committed it, that commit, the Modules and whether the architecture this run recorded. workflow is the object of Workflows' step output convention, which defines its fields: one review note whose data holds the verdict and each Module's outcome with its count of blocking Issues that stand. Findings, tiers, severities and resolutions inside each review are worker claims; everything else is the Operation's. A behaviour or field change increments the version.",
  "example": {
    "verdict": "changes_required",
    "full": false,
    "validation": {
      "errors": 0,
      "warnings": 1
    },
    "checks": [
      {
        "check": "check.checkout.tests",
        "module": "module.checkout",
        "outcome": "failed",
        "exit_code": 1,
        "log": "/home/dev/shop/.concorde/unbound/r-20261007T090000-project_review-1a2b3c4d/checks/check.checkout.tests/output.log"
      }
    ],
    "deterministic": {
      "complete": true,
      "findings": [
        {
          "phase": "check",
          "module": "module.checkout",
          "title": "Configured check check.checkout.tests does not pass",
          "tier": "obvious-fix",
          "severity": "high",
          "subjects": [
            "check.checkout.tests"
          ],
          "issue": "I-0123456789abcdef0123456789abcdef"
        }
      ],
      "unowned": [],
      "earlier_issues": {
        "carried": [],
        "resolved": []
      }
    },
    "architecture": {
      "state": "skipped",
      "complete": true,
      "context_identity": "sha256:4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d",
      "review": null
    },
    "modules": [
      {
        "module": "module.checkout",
        "outcome": "changes_required",
        "identities": {
          "spec": "sha256:1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a",
          "code": "sha256:2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
          "code_digest": "sha256:3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c"
        },
        "panel": {
          "state": "skipped",
          "review": null
        },
        "code_review": {
          "state": "reviewed",
          "review": {
            "module": "module.checkout",
            "outcome": "changes_required",
            "context_identity": "sha256:2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
            "summary": "The total ignores the discount the Spec requires.",
            "findings": [
              {
                "module": "module.checkout",
                "kind": "violation",
                "severity": "high",
                "tier": "obvious-fix",
                "title": "The total ignores the discount",
                "problem": "total() adds the prices without the discount.",
                "impact": "Every discounted order is overcharged.",
                "basis": "req.checkout.discount",
                "locations": [
                  "src/checkout/total.py:12-18"
                ],
                "evidence": "total.py:15 returns sum(prices).",
                "suggestion": "Subtract the discount before returning.",
                "issue": "I-1123456789abcdef0123456789abcdef"
              }
            ],
            "rejected": [],
            "earlier_issues": {
              "carried": [],
              "resolved": [],
              "ignored": []
            }
          }
        },
        "standing": [
          {
            "issue": "I-0123456789abcdef0123456789abcdef",
            "severity": "high",
            "tier": "obvious-fix",
            "title": "Configured check check.checkout.tests does not pass"
          },
          {
            "issue": "I-1123456789abcdef0123456789abcdef",
            "severity": "high",
            "tier": "obvious-fix",
            "title": "The total ignores the discount"
          }
        ]
      },
      {
        "module": "module.inventory",
        "outcome": "accepted",
        "identities": {
          "spec": "sha256:5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e",
          "code": "sha256:6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f",
          "code_digest": "sha256:7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a"
        },
        "panel": {
          "state": "skipped",
          "review": null
        },
        "code_review": {
          "state": "skipped",
          "review": null
        },
        "standing": [
          {
            "issue": "I-2123456789abcdef0123456789abcdef",
            "severity": "low",
            "tier": "suggestion",
            "title": "The reservation section could name its actor"
          }
        ]
      }
    ],
    "standing": {
      "issues": 3,
      "blocking": 2,
      "by_severity": {
        "critical": 0,
        "high": 2,
        "medium": 0,
        "low": 1,
        "unrated": 0
      },
      "by_tier": {
        "suggestion": 1,
        "obvious-fix": 2,
        "preferred-fix": 0,
        "decision-needed": 0,
        "unrated": 0
      }
    },
    "record": {
      "path": ".concorde/reviews/record.json",
      "published": true,
      "commit": "9f8e7d6c5b4a39281706f5e4d3c2b1a09f8e7d6c",
      "modules": [
        "module.checkout"
      ],
      "architecture": false
    },
    "workflow": {
      "decision_points": [],
      "decisions": [],
      "deviations": [],
      "notes": [
        {
          "kind": "review",
          "text": "project_review verdict changes_required: module.checkout changes_required, module.inventory accepted",
          "data": {
            "verdict": "changes_required",
            "modules": [
              {
                "module": "module.checkout",
                "outcome": "changes_required",
                "blocking": 2
              },
              {
                "module": "module.inventory",
                "outcome": "accepted",
                "blocking": 0
              }
            ]
          }
        }
      ],
      "blocking": null,
      "data": {}
    }
  }
}
```

## Review record

```concorde-contract
{
  "id": "contract.project-review.record",
  "version": 1,
  "schema": {
    "type": "object",
    "additionalProperties": false,
    "required": [
      "schema_version",
      "architecture",
      "modules"
    ],
    "properties": {
      "schema_version": {
        "const": 1
      },
      "architecture": {
        "anyOf": [
          {
            "type": "null"
          },
          {
            "type": "object",
            "additionalProperties": false,
            "required": [
              "context_identity",
              "run",
              "commit",
              "judged_at"
            ],
            "properties": {
              "context_identity": {
                "type": "string",
                "pattern": "^sha256:[0-9a-f]{64}$"
              },
              "run": {
                "type": "string",
                "minLength": 1
              },
              "commit": {
                "anyOf": [
                  {
                    "type": "string",
                    "minLength": 1
                  },
                  {
                    "type": "null"
                  }
                ]
              },
              "judged_at": {
                "type": "string",
                "minLength": 1
              },
              "resolved": {
                "type": "array",
                "items": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": [
                    "issue",
                    "revision"
                  ],
                  "properties": {
                    "issue": {
                      "type": "string",
                      "pattern": "^I-[0-9a-f]{32}$"
                    },
                    "revision": {
                      "type": "string",
                      "pattern": "^sha256:[0-9a-f]{64}$"
                    }
                  }
                }
              }
            }
          }
        ]
      },
      "modules": {
        "type": "object",
        "additionalProperties": {
          "type": "object",
          "additionalProperties": false,
          "properties": {
            "panel": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "context_identity",
                "run",
                "commit",
                "judged_at"
              ],
              "properties": {
                "context_identity": {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                "run": {
                  "type": "string",
                  "minLength": 1
                },
                "commit": {
                  "anyOf": [
                    {
                      "type": "string",
                      "minLength": 1
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "judged_at": {
                  "type": "string",
                  "minLength": 1
                },
                "resolved": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "issue",
                      "revision"
                    ],
                    "properties": {
                      "issue": {
                        "type": "string",
                        "pattern": "^I-[0-9a-f]{32}$"
                      },
                      "revision": {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$"
                      }
                    }
                  }
                }
              }
            },
            "code_review": {
              "type": "object",
              "additionalProperties": false,
              "required": [
                "context_identity",
                "code_digest",
                "run",
                "commit",
                "judged_at"
              ],
              "properties": {
                "context_identity": {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                "code_digest": {
                  "type": "string",
                  "pattern": "^sha256:[0-9a-f]{64}$"
                },
                "run": {
                  "type": "string",
                  "minLength": 1
                },
                "commit": {
                  "anyOf": [
                    {
                      "type": "string",
                      "minLength": 1
                    },
                    {
                      "type": "null"
                    }
                  ]
                },
                "judged_at": {
                  "type": "string",
                  "minLength": 1
                },
                "resolved": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "issue",
                      "revision"
                    ],
                    "properties": {
                      "issue": {
                        "type": "string",
                        "pattern": "^I-[0-9a-f]{32}$"
                      },
                      "revision": {
                        "type": "string",
                        "pattern": "^sha256:[0-9a-f]{64}$"
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  },
  "semantics": "The review record, .concorde/reviews/record.json of the primary branch, the one file in which project_review keeps what its last review of each part judged. architecture is null until an architecture review completed; otherwise context_identity is the review-architecture context identity of every Module it judged. modules maps a Module identity to its parts: panel holds the context identity of the Module's review-spec grant its last completed Spec panel judged, code_review the context identity of its review-code grant and code_digest the digest of the paths and bytes of the files it bound when its last completed code review judged it. Every entry names the run that judged it, the commit an unbound run examined, null for a run in a bound workspace, judged_at, the UTC time the run recorded it, and resolved, present only when the part found earlier Issues resolved that were still open when the run ended, each with the revision it had then: while that revision is unchanged, a run that skips the part counts the Issue resolved. A part is recorded only once its workers finished and all of its Issues were written; a later run merges its own entries over the earlier ones and keeps every other. A behaviour or field change increments the version.",
  "example": {
    "schema_version": 1,
    "architecture": {
      "context_identity": "sha256:4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d4d",
      "run": "r-20261006T170000-project_review-0a1b2c3d",
      "commit": "1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e",
      "judged_at": "2026-10-06T17:42:10Z"
    },
    "modules": {
      "module.checkout": {
        "panel": {
          "context_identity": "sha256:1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a1a",
          "run": "r-20261006T170000-project_review-0a1b2c3d",
          "commit": "1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e",
          "judged_at": "2026-10-06T17:40:02Z"
        },
        "code_review": {
          "context_identity": "sha256:2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b2b",
          "code_digest": "sha256:3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c3c",
          "run": "r-20261007T090000-project_review-1a2b3c4d",
          "commit": "2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f",
          "judged_at": "2026-10-07T09:12:44Z",
          "resolved": [
            {
              "issue": "I-3123456789abcdef0123456789abcdef",
              "revision": "sha256:8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b8b"
            }
          ]
        }
      },
      "module.inventory": {
        "panel": {
          "context_identity": "sha256:5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e5e",
          "run": "r-20261006T170000-project_review-0a1b2c3d",
          "commit": "1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e",
          "judged_at": "2026-10-06T17:39:51Z"
        },
        "code_review": {
          "context_identity": "sha256:6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f6f",
          "code_digest": "sha256:7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a7a",
          "run": "r-20261006T170000-project_review-0a1b2c3d",
          "commit": "1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e",
          "judged_at": "2026-10-06T17:41:30Z"
        }
      }
    }
  }
}
```
