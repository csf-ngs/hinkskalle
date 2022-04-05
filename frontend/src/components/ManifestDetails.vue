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
                <v-icon>mdi-content-copy</v-icon>
                {{tag | abbreviate(20)}}
            </v-chip>
          </span>
        </v-col>
        <v-col md="auto" class="d-flex justify-center align-center">
          <span v-if="manifest.filename!=='(none)'">
            <span v-if="manifest.type === 'singularity' || manifest.type === 'oras'" class="mr-2">
              <v-menu offset-y>
                <template v-slot:activator="{ on, attrs }">
                  <v-btn raised class="download-button" v-bind="attrs" v-on="on">
                    <span style="margin-right: 0.2rem;">
                      {{manifest.filename}}: {{manifest.total_size | prettyBytes() }}
                    </span>
                    <v-badge :content="localState.downloadCount || '0'" :color="badgeColor">
                      <v-icon>mdi-download</v-icon>
                    </v-badge>
                  </v-btn>
                </template>
                <v-list>
                  <v-list-item @click.stop="downloadManifest()">
                    <v-list-item-icon><v-icon>mdi-download</v-icon></v-list-item-icon>
                    <v-list-item-content>Download</v-list-item-content>
                  </v-list-item>
                  <v-list-item @click.stop="copyDownload()">
                    <v-list-item-icon><v-icon>mdi-content-copy</v-icon></v-list-item-icon>
                    <v-list-item-content>Copy URL</v-list-item-content>
                  </v-list-item>
                  <v-list-item @click.stop="copyDownload('curl')">
                    <v-list-item-icon><v-icon>mdi-bash</v-icon></v-list-item-icon>
                    <v-list-item-content>Copy cURL</v-list-item-content>
                  </v-list-item>
                  <v-list-item @click.stop="copyDownload('wget')">
                    <v-list-item-icon><v-icon>mdi-bash</v-icon></v-list-item-icon>
                    <v-list-item-content>Copy wget</v-list-item-content>
                  </v-list-item>
                </v-list>
              </v-menu>
            </span>
            <span v-else>
              <span class="font-weight-medium">Filename:</span> {{manifest.filename}}&nbsp;|&nbsp;
              {{manifest.total_size | prettyBytes() }}
              <v-badge :content="localState.downloadCount || '0'" :color="badgeColor">
                <v-icon>mdi-download</v-icon>
              </v-badge>
            </span>
          </span>
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
<style lang="scss">
button.download-button {
  letter-spacing: inherit;
  text-transform: none;
  font-family: "Roboto Mono", monospace;
}
</style>
<script lang="ts">
import { Image, Manifest } from '@/store/models';
import DockerDetails from '@/components/DockerDetails.vue';
import SingularityDetails from '@/components/SingularityDetails.vue';
import OrasDetails from '@/components/OrasDetails.vue';
import Vue from 'vue';

interface State {
  image?: Image;
  downloadCount: number;
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
      downloadCount: 0,
    },
  }),
  mounted: function() {
    this.localState.downloadCount = this.manifest.downloadCount;
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
  computed: {
    badgeColor() {
      return this.localState.downloadCount ?
        'blue darken-1' : 'blue-grey lighten-1'
    }
  },
  methods: {
    copyTag(tag: string) {
      this.$copyText(this.manifest.pullCmd(tag))
        .then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard"))
    },
    downloadManifest() {
      this.$store.dispatch('tokens/requestDownload', { id: this.manifest.id, type: 'manifest' })
        .then((location: string) => {
          window.location.href=location;
          // cheating
          this.localState.downloadCount++;
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        });
    },
    copyDownload(what: string | null = null) {
      this.$store.dispatch('tokens/requestDownload', { id: this.manifest.id, type: 'manifest' })
        .then((location: string) => {
          switch(what) {
            case 'curl':
              location = `curl -JOf ${location}`;
              break;
            case 'wget':
              location = `wget -O ${this.manifest.filename} ${location}`
              break;
          }
          this.$copyText(location).then(() => this.$store.commit('snackbar/showSuccess', "Copied to clipboard"))
        })
        .catch(err => {
          this.$store.commit('snackbar/showError', err);
        })
    }
  },
});
</script>