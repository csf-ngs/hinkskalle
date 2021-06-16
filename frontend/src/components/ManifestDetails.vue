<template>
  <v-expansion-panel v-if="manifest">
    <v-expansion-panel-header>
      <v-row no-gutters justify="space-between">
        <v-col>
          <span v-if="manifest.tags.length==0">
            <v-chip color="yellow lighten-2">
              <v-icon left>mdi-alert-circle-outline</v-icon>
              No tags
            </v-chip>
          </span>
          <span>
            <v-chip
              color="green lighten-1"
              v-for="tag in manifest.tags" :key="tag"
              @click.stop="copyTag(tag)">
                {{tag}}
            </v-chip>
          </span>
        </v-col>
        <v-col md="auto" class="d-flex justify-center align-center">
          <span v-if="manifest.filename!=='(none)'">
            <span class="font-weight-medium">Filename:</span> {{manifest.filename}}&nbsp;|&nbsp;
          </span>
          <span class="font-weight-medium">Size:</span> {{manifest.total_size | prettyBytes() }}
        </v-col>
        <v-col class="d-flex justify-end align-center mr-4">
          <div v-if="manifest.type=='singularity'">
            <img src="/singularity-logo.png" style="height: 1.2rem;">
            Singularity
          </div>
          <div v-else-if="manifest.type=='docker'">
            <img src="/docker-logo.png" style="height: 1.2rem;">
            Docker
          </div>
          <div v-else-if="manifest.type=='oci'">
            <img src="/oci-logo.png" style="height: 1.2rem;">
            OCI
          </div>
          <div v-else-if="manifest.type=='oras'">
            <img src="/oras-logo.png" style="height: 1.2rem;">
            ORAS
          </div>
          <div v-else-if="manifest.type=='other'">
            <v-icon>mdi-file-question</v-icon>
            Other/Unknown
          </div>
          <div v-else-if="manifest.type=='invalid'">
            <v-icon color="error">mdi-file-cancel-outline</v-icon>
            Invalid Config
          </div>

        </v-col>
      </v-row>
    </v-expansion-panel-header>
    <v-expansion-panel-content v-if="manifest.type=='docker' || manifest.type=='oci'">
      <docker-details :manifest="manifest"></docker-details>
    </v-expansion-panel-content>
    <v-expansion-panel-content v-if="manifest.type=='singularity'">
      <singularity-details :image="localState.image"></singularity-details>
    </v-expansion-panel-content>
    <v-expansion-panel-content v-if="manifest.type=='oras'">
      <oras-details :manifest="manifest"></oras-details>
    </v-expansion-panel-content>
  </v-expansion-panel>
</template>
<script lang="ts">
import { Image, Manifest } from '@/store/models';
import DockerDetails from '@/components/DockerDetails.vue';
import SingularityDetails from '@/components/SingularityDetails.vue';
import OrasDetails from '@/components/OrasDetails.vue';
import Vue from 'vue';

interface State {
  image?: Image;
}

export default Vue.extend({
  components: { DockerDetails, SingularityDetails, OrasDetails },
  name: 'ManifestDetails',
  props: {
    manifest: {
      type: Manifest,
      required: true,
    },
    readonly: {
      type: Boolean,
      default: false,
    },
  },
  data: (): { localState: State } => ({
    localState: {
      image: undefined,
    },
  }),
  mounted: function() {
    if (this.manifest.type !== 'singularity') {
      return;
    }
    this.$store.dispatch('images/get', { path: this.manifest.path, tag: this.manifest.content.layers[0].digest.replace('sha256:', 'sha256.')  })
      .then(image => {
        this.localState.image = image;
      })
      .catch(err => {
        this.$store.commit('snackbar/showError', err);
      });
  },
  methods: {
    copyTag(tag: string) {
      this.$copyText(this.manifest.pullCmd(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard"))
    }
  },
});
</script>