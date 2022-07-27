# -*- coding: utf-8 -*-
# @Author: gonglinxiao
# @Date:   2022-07-08 20:05:15
# @Last Modified time: 2022-07-11 20:28:18

from enum import Enum, unique

# track the state of other clients, from the perspective of this client.
@unique
class OtherClientState(Enum):
	kAlive = 0
	kDeadAtRound1 = 1
	kDeadAtRound2 = 2
	kDeadAtRound3 = 3

@unique
class ClientState(Enum):
	INITIAL = 0
	R0_ADVERTISE_KEYS = 1
	R1_SHARE_KEYS = 2
	R2_MASKED_INPUT = 3
	R3_UNMASKING = 4
	COMPLETED = 5
	ABORTED = 6