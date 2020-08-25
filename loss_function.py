import torch
from torch import nn
from torch.distributions.kl import kl_divergence as kld
from torch.distributions.categorical import Categorical
from torch.distributions.normal import Normal


class Tacotron2Loss(nn.Module):
    def __init__(self, hparams):
        super(Tacotron2Loss, self).__init__()
        self.ce_loss = nn.CrossEntropyLoss()

    def forward(self, model_output, targets, re, batched_speakers):
        mel_target, gate_target = targets[0], targets[1]
        mel_target.requires_grad = False
        gate_target.requires_grad = False
        gate_target = gate_target.view(-1, 1)

        (
            mel_out,
            mel_out_postnet,
            gate_out,
            alignments,
            spkr_clsfir_logits,
        ) = model_output
        gate_out = gate_out.view(-1, 1)
        mel_loss = nn.MSELoss()(mel_out, mel_target) + nn.MSELoss()(
            mel_out_postnet, mel_target
        )
        gate_loss = nn.BCEWithLogitsLoss()(gate_out, gate_target)

        means, stddevs = re.q_zo_given_X_at_x.mean, re.q_zo_given_X_at_x.stddev
        kl_loss = kld(
            Normal(means[0], stddevs[0]),
            re.p_zo_given_yo.distrib_lis[batched_speakers[0]],
        ).mean()
        for i, speaker in enumerate(batched_speakers[1:], 1):
            kl_loss += kld(
                Normal(means[i], stddevs[i]), re.p_zo_given_yo.distrib_lis[speaker]
            ).mean()
        #        print("speaker kl loss:- ", kl_loss/batched_speakers.shape[0])
        for i in range(re.p_zl_given_yl.n_disc):
            ans = (
                re.q_yl_given_X[i]
                * kld(re.q_zl_given_X_at_x, re.p_zl_given_yl.distrib_lis[i]).mean(dim=1)
            ).sum()
            # print("Difference in i-th dimension of residual :- ", ans, re.q_yl_given_X[i])
            kl_loss += ans
        #        print("speaker+resdiual kl loss:- ", kl_loss/batched_speakers.shape[0])
        for i in range(re.q_yl_given_X.shape[1]):
            kl_loss += kld(Categorical(re.q_yl_given_X[:, i]), re.y_l)
        kl_loss = kl_loss / batched_speakers.shape[0]

        index_into_spkr_logits = batched_speakers.repeat_interleave(
            spkr_clsfir_logits.shape[1]
        )
        spkr_clsfir_logits = spkr_clsfir_logits.reshape(
            -1, spkr_clsfir_logits.shape[-1]
        )
        mask_index = spkr_clsfir_logits.abs().sum(dim=1) != 0
        spkr_clsfir_logits = spkr_clsfir_logits[mask_index]
        index_into_spkr_logits = index_into_spkr_logits[mask_index]
        speaker_loss = self.ce_loss(
            spkr_clsfir_logits, index_into_spkr_logits
        )  # /batched_speakers.shape[0]

        print("Mel Loss:- ", mel_loss)
        #        print("gate_loss :- ", gate_loss)
        #        print("speaker_loss :- ", speaker_loss)
        print("kl loss:- ", kl_loss)
        #        print("Total Loss:- ", (mel_loss + gate_loss) + 0.02*speaker_loss +kl_loss)

        return (50 * mel_loss + gate_loss) + 0.02 * speaker_loss + kl_loss
